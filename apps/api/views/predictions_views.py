"""
apps.api.views.predictions_views

Predictions are read-only as directly-created objects (list/retrieve) —
the only way to CREATE one is the custom `request/` action below, which
runs the actual trained model rather than accepting a client-supplied
compatibility_score. This mirrors the web UI's PredictionCreateView
(apps.predictions.views), which is also not a plain ModelForm save.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import Profile
from apps.api.permissions import IsAdminOrCaseWorkerOrReadOnly
from apps.api.serializers.predictions_serializers import PredictionRequestSerializer, PredictionSerializer
from apps.predictions.models import Prediction
from ml.inference.predict import ModelNotTrainedError, predict_compatibility


class PredictionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Prediction.objects.select_related("child", "family", "predicted_by").order_by("-created_at")
    serializer_class = PredictionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["child", "family", "model_name"]

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def request_prediction(self, request):
        """
        POST /api/v1/predictions/request_prediction/
        Body: {"child": <id>, "family": <id>}

        Runs the actual persisted Step 9 model (ml.inference.predict) —
        identical code path to the web UI's PredictionCreateView, so the
        API and the web app can never silently disagree on how a
        prediction is computed.
        """
        input_serializer = PredictionRequestSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        child = input_serializer.validated_data["child"]
        family = input_serializer.validated_data["family"]

        try:
            result = predict_compatibility(child, family)
        except ModelNotTrainedError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        prediction = Prediction.objects.create(
            child=child,
            family=family,
            compatibility_score=result["compatibility_score"],
            model_name=result["model_name"],
            model_version="v1",
            predicted_by=request.user,
            explanation_data=result.get("explanation", {}),
        )

        output_serializer = PredictionSerializer(prediction)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
