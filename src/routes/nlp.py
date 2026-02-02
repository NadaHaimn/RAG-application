from fastapi import APIRouter, status, Request, Depends
from fastapi.responses import JSONResponse
from helpers.security import verify_api_key
from routes.schemes.nlp import SearchRequest
from models.ProjectModel import ProjectModel
from controllers import NLPController
from models import ResponseSignal
import logging

logger = logging.getLogger('uvicorn.error')

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_v1", "nlp"],
)


@nlp_router.post("/answer/{project_id}")
async def answer_rag(
    request: Request,
    project_id: str,
    search_request: SearchRequest,
    api_key: str = Depends(verify_api_key)  # ← Security: API Key verification
):
    # ─── Project ────────────────────────────────────
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )
    project = await project_model.get_project_or_create(
        project_id=project_id
    )

    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseSignal.PROJECT_NOT_FOUND_ERROR.value}
        )

    # ─── NLP Controller ─────────────────────────────
    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    # ─── الـ search بيحصل داخل answer_rag_question تلقائياً ─
    answer, full_prompt, chat_history = nlp_controller.answer_rag_question(
        project=project,
        query=search_request.text,
        limit=search_request.limit,
    )

    if not answer:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseSignal.RAG_ANSWER_ERROR.value}
        )

    return JSONResponse(
        content={
            "signal": ResponseSignal.RAG_ANSWER_SUCCESS.value,
            "answer": answer,
            "full_prompt": full_prompt,
            "chat_history": chat_history
        }
    )
