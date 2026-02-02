from fastapi import APIRouter, Depends, UploadFile, status, Request, Form
from fastapi.responses import JSONResponse
import os
from helpers.config import get_settings, Settings
from controllers import DataController, ProjectController, ProcessController, NLPController
import aiofiles
from models import ResponseSignal
import logging
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from models.AssetModel import AssetModel
from models.db_schemes import DataChunk, Asset
from models.enums.AssetTypeEnum import AssetTypeEnum
from typing import Optional

logger = logging.getLogger('uvicorn.error')

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"]
)


@data_router.post("/ingest/{project_id}")
async def ingest_data(
    request: Request,
    project_id: str,
    file: UploadFile,
    chunk_size: Optional[int] = Form(default=100),
    overlap: Optional[int] = Form(default=20),
    do_reset: Optional[int] = Form(default=0),
    do_index: Optional[int] = Form(default=1),  # بـ default يـ index فوراً بعد الـ upload والـ process
    app_settings: Settings = Depends(get_settings)
):
    # ─── Step 1: Project ────────────────────────────
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )
    project = await project_model.get_project_or_create(
        project_id=project_id
    )

    # ─── Step 2: Validate File ──────────────────────
    data_controller = DataController()
    is_valid, result_signal = data_controller.validate_file_properties(file=file)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": result_signal}
        )

    # ─── Step 3: Upload File ────────────────────────
    file_path, file_id = data_controller.generate_unique_filepath(
        orig_file_name=file.filename,
        project_id=project_id
    )

    try:
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:
        logger.error(f"Error while uploading file: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseSignal.FILE_UPLOAD_FAILED.value}
        )

    # ─── Step 4: Save Asset Record ──────────────────
    asset_model = await AssetModel.create_instance(
        db_client=request.app.db_client
    )
    asset_resource = Asset(
        asset_project_id=project.id,
        asset_type=AssetTypeEnum.FILE.value,
        asset_name=file_id,
        asset_size=os.path.getsize(file_path)
    )
    asset_record = await asset_model.create_asset(asset=asset_resource)

    # ─── Step 5: Process (Chunking) ─────────────────
    process_controller = ProcessController(project_id=project_id)

    file_content = process_controller.get_file_content(file_id=file_id)
    if file_content is None:
        logger.error(f"Error while reading file content: {file_id}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseSignal.PROCESSING_FAILED.value}
        )

    file_chunks = process_controller.process_file_content(
        file_content=file_content,
        file_id=file_id,
        chunk_size=chunk_size,
        overlap_size=overlap
    )

    if not file_chunks or len(file_chunks) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseSignal.PROCESSING_FAILED.value}
        )

    # ─── Step 6: Save Chunks to DB ──────────────────
    chunk_model = await ChunkModel.create_instance(
        db_client=request.app.db_client
    )

    if do_reset == 1:
        await chunk_model.delete_chunks_by_project_id(project_id=project.id)

    file_chunks_records = [
        DataChunk(
            chunk_text=chunk.page_content,
            chunk_metadata=chunk.metadata,
            chunk_order=i + 1,
            chunk_project_id=project.id,
            chunk_asset_id=asset_record.id
        )
        for i, chunk in enumerate(file_chunks)
    ]

    inserted_chunks = await chunk_model.insert_many_chunks(chunks=file_chunks_records)

    # ─── Step 7: Index into Vector DB (اختياري) ─────
    indexed_items = 0
    if do_index == 1:
        nlp_controller = NLPController(
            vectordb_client=request.app.vectordb_client,
            generation_client=request.app.generation_client,
            embedding_client=request.app.embedding_client,
            template_parser=request.app.template_parser,
        )

        # جيب الـ chunks صفحة صفحة وـ index them
        page_no = 1
        idx = 0
        is_first_page = True

        while True:
            page_chunks = await chunk_model.get_poject_chunks(
                project_id=project.id, page_no=page_no
            )

            # لو الصفحة فارغة خلصت
            if not page_chunks or len(page_chunks) == 0:
                break

            chunks_ids = list(range(idx, idx + len(page_chunks)))
            idx += len(page_chunks)

            # الـ do_reset بيـ apply بس في الصفحة الأولى
            is_inserted = nlp_controller.index_into_vector_db(
                project=project,
                chunks=page_chunks,
                do_reset=(do_reset == 1 and is_first_page),
                chunks_ids=chunks_ids
            )
            is_first_page = False

            if not is_inserted:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"signal": ResponseSignal.INSERT_INTO_VECTORDB_ERROR.value}
                )

            indexed_items += len(page_chunks)
            page_no += 1

    # ─── Response ───────────────────────────────────
    return JSONResponse(
        content={
            "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
            "file_id": str(asset_record.id),
            "inserted_chunks": inserted_chunks,
            "indexed_items": indexed_items,
            "is_indexed": do_index == 1
        }
    )
