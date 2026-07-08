from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AssessmentAnswerViewSet,
    AssessmentDimensionViewSet,
    AssessmentFrameworkViewSet,
    AssessmentQuestionViewSet,
    AssessmentViewSet,
    MaturityScoreViewSet,
    RecommendationViewSet,
)

router = DefaultRouter()
router.register("assessment-frameworks", AssessmentFrameworkViewSet, basename="assessment-framework")
router.register("assessment-dimensions", AssessmentDimensionViewSet, basename="assessment-dimension")
router.register("assessment-questions", AssessmentQuestionViewSet, basename="assessment-question")
router.register("assessments", AssessmentViewSet, basename="assessment")
router.register("assessment-answers", AssessmentAnswerViewSet, basename="assessment-answer")
router.register("maturity-scores", MaturityScoreViewSet, basename="maturity-score")
router.register("recommendations", RecommendationViewSet, basename="recommendation")

urlpatterns = [
    path("", include(router.urls)),
]
