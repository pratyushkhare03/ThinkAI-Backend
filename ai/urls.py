from django.urls import path
from .views import chat, process_notes, generate_quiz, generate_flashcards, generate_summary, compare_summaries, extract_keywords

urlpatterns = [
    path("chat/", chat),
    path("process-notes/", process_notes),
    path("generate-quiz/", generate_quiz),
    path("generate-flashcards/", generate_flashcards),
    path("generate-summary/", generate_summary),
]