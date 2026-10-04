"""IMP-051 concrete Flow / Omni provider adapters.

Provider-specific payloads and legacy transport calls are intentionally confined
here.  The canonical ``agent.studio`` layer sees only provider-neutral plans and
normalized observations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Awaitable, Callable

from agent.studio.provider_adapter import (
    ProviderAdapterPort,
    ProviderAdapterUnsupported,
    ProviderExecutionMode,
    ProviderExecutionPlan,
    ProviderHandleKind,
    ProviderObservationKind,
    ProviderObservationState,
    ProviderTransportHandle,
    ProviderTransportObservation,
)


def _aspect(value: str) -> str:
    normalized = str(value).strip().lower().replace(" ", "")
    if normalized in {"16:9", "landscape", "video_aspect_ratio_landscape"}:
        return "VIDEO_ASPECT_RATIO_LANDSCAPE"
    if normalized in {"9:16", "portrait", "video_aspect_ratio_portrait"}:
        return "VIDEO_ASPECT_RATIO_PORTRAIT"
    raise ProviderAdapterUnsupported(f"unsupported provider aspect ratio: {value}")


def _omni_transport_model_key(
    mode: ProviderExecutionMode,
    duration_seconds: int,
    resolution: str,
) -> str:
    resolution = str(resolution).strip().lower()
    if duration_seconds not in {4, 6, 8, 10}:
        raise ProviderAdapterUnsupported(
            f"unsupported Omni Flash duration: {duration_seconds}s"
        )
    if resolution not in {"360p", "720p"}:
        raise ProviderAdapterUnsupported(
            f"unsupported Omni Flash resolution: {resolution}"
        )
    suffix = "_360p" if resolution == "360p" else ""
    prefixes = {
        ProviderExecutionMode.TEXT_TO_VIDEO: "abra_t2v_",
        ProviderExecutionMode.FIRST_FRAME_TO_VIDEO: "abra_i2v_",
        ProviderExecutionMode.FIRST_LAST_FRAME_TO_VIDEO: "omni_flash_i2v_",
        ProviderExecutionMode.REFERENCES_TO_VIDEO: "abra_r2v_",
    }
    prefix = prefixes[mode]
    if mode is ProviderExecutionMode.FIRST_LAST_FRAME_TO_VIDEO:
        return f"{prefix}{duration_seconds}s_first_last{suffix}"
    return f"{prefix}{duration_seconds}s{suffix}"


def _error_text(result: Any) -> str | None:
    if not isinstance(result, dict):
        return "provider returned non-object response"
    error = result.get("error")
    if error:
        return str(error)
    status = result.get("status")
    if isinstance(status, int) and status >= 400:
        return f"provider returned HTTP-like status {status}"
    return None


def _first_operation(result: dict) -> dict | None:
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    operations = data.get("operations") if isinstance(data, dict) else None
    if not isinstance(operations, list) or not operations:
        return None
    return operations[0] if isinstance(operations[0], dict) else None


def _operation_id(operation: dict | None) -> str | None:
    if not operation:
        return None
    nested = operation.get("operation")
    if isinstance(nested, dict) and nested.get("name"):
        return str(nested["name"])
    if operation.get("name"):
        return str(operation["name"])
    return None


def _operation_media(operation: dict | None) -> tuple[str | None, str | None]:
    if not operation:
        return None, None
    media = operation.get("media")
    if not isinstance(media, dict):
        return None, None
    media_id = media.get("media_id") or media.get("name")
    url = media.get("url") or media.get("fifeUrl")
    return (
        str(media_id) if media_id else None,
        str(url) if url else None,
    )


def _normalize_operation_poll(
    *,
    provider_key: str,
    result: Any,
    handle: ProviderTransportHandle,
    observed_at: datetime,
    kind: ProviderObservationKind,
) -> ProviderTransportObservation:
    error = _error_text(result)
    if error:
        return ProviderTransportObservation(
            provider_key=provider_key,
            kind=kind,
            state=ProviderObservationState.AMBIGUOUS,
            observed_at=observed_at,
            handle=handle,
            error_class="TRANSPORT_POLL_ERROR",
            message=error,
            side_effect_may_have_occurred=True,
            retry_safe=False,
        )
    operation = _first_operation(result if isinstance(result, dict) else {})
    if operation is None:
        return ProviderTransportObservation(
            provider_key=provider_key,
            kind=kind,
            state=ProviderObservationState.AMBIGUOUS,
            observed_at=observed_at,
            handle=handle,
            error_class="UNRECOGNIZED_POLL_RESPONSE",
            message="provider poll response did not contain a recognizable operation",
            side_effect_may_have_occurred=True,
            retry_safe=False,
        )
    status = str(operation.get("status") or "").upper()
    media_id, url = _operation_media(operation)
    if "SUCCESS" in status and (media_id or url):
        return ProviderTransportObservation(
            provider_key=provider_key,
            kind=kind,
            state=ProviderObservationState.SUCCEEDED,
            observed_at=observed_at,
            handle=handle,
            output_media_id=media_id,
            output_url=url,
            retry_safe=False,
        )
    if "FAIL" in status:
        return ProviderTransportObservation(
            provider_key=provider_key,
            kind=kind,
            state=ProviderObservationState.FAILED,
            observed_at=observed_at,
            handle=handle,
            error_class="PROVIDER_REPORTED_FAILURE",
            message=str(operation.get("error") or "provider reported generation failure"),
            side_effect_may_have_occurred=True,
            retry_safe=False,
        )
    return ProviderTransportObservation(
        provider_key=provider_key,
        kind=kind,
        state=ProviderObservationState.PENDING,
        observed_at=observed_at,
        handle=handle,
        side_effect_may_have_occurred=True,
        retry_safe=False,
    )


class FlowVideoProviderAdapter(ProviderAdapterPort):
    def __init__(
        self,
        *,
        provider_key: str,
        flow_client: Any,
        runtime_project_id: str,
        dialect_bindings: dict[tuple[str, int, str], str],
    ) -> None:
        self.provider_key = str(provider_key).strip()
        self._client = flow_client
        self._runtime_project_id = str(runtime_project_id).strip()
        self._dialect_bindings = {
            (str(model).strip(), int(duration), str(resolution).strip().lower()): str(tier).strip()
            for (model, duration, resolution), tier in dialect_bindings.items()
            if str(model).strip() and str(resolution).strip() and str(tier).strip()
        }
        if not self.provider_key or not self._runtime_project_id:
            raise ValueError("Flow adapter requires provider_key and runtime_project_id")
        if not self._dialect_bindings:
            raise ValueError("Flow adapter requires explicit exact dialect bindings")

    async def submit(
        self, plan: ProviderExecutionPlan, *, observed_at: datetime
    ) -> ProviderTransportObservation:
        if plan.provider_key != self.provider_key:
            return self._unsupported(plan, observed_at, "plan selected a different provider")
        if plan.mode is not ProviderExecutionMode.FIRST_FRAME_TO_VIDEO:
            return self._unsupported(
                plan,
                observed_at,
                "current FlowClient has no proven non-degraded payload for this mode",
            )
        if len(plan.runtime_references) != 1:
            return self._unsupported(
                plan,
                observed_at,
                "Flow first-frame mode requires exactly one runtime reference",
            )
        dialect_key = (
            plan.model_version,
            plan.duration_seconds,
            plan.resolution.strip().lower(),
        )
        tier = self._dialect_bindings.get(dialect_key)
        if tier is None:
            return self._unsupported(
                plan,
                observed_at,
                "Flow model/duration/resolution tuple has no proven exact transport binding",
            )
        try:
            aspect = _aspect(plan.aspect_ratio)
        except ProviderAdapterUnsupported as exc:
            return self._unsupported(plan, observed_at, str(exc))
        try:
            actual_model = self._client._batch_video_model(tier, "frame_2_video", aspect)
        except Exception as exc:
            return self._unsupported(
                plan,
                observed_at,
                f"Flow transport model mapping could not be proven: {type(exc).__name__}: {exc}",
            )
        if actual_model != plan.model_version:
            return self._unsupported(
                plan,
                observed_at,
                f"Flow transport would lower to {actual_model!r}, not selected model {plan.model_version!r}",
            )
        try:
            result = await self._client.generate_video(
                start_image_media_id=plan.runtime_references[0].media_id,
                prompt=plan.prompt,
                project_id=self._runtime_project_id,
                scene_id=plan.shot_ir_ref.logical_id.root,
                aspect_ratio=aspect,
                user_paygate_tier=tier,
            )
        except Exception as exc:
            return self._ambiguous_submit(observed_at, exc)
        error = _error_text(result)
        if error:
            return ProviderTransportObservation(
                provider_key=self.provider_key,
                kind=ProviderObservationKind.SUBMIT,
                state=ProviderObservationState.AMBIGUOUS,
                observed_at=observed_at,
                error_class="SUBMIT_RESULT_ERROR",
                message=error,
                side_effect_may_have_occurred=True,
                retry_safe=False,
            )
        operation = _first_operation(result)
        op_id = _operation_id(operation)
        if not op_id:
            return ProviderTransportObservation(
                provider_key=self.provider_key,
                kind=ProviderObservationKind.SUBMIT,
                state=ProviderObservationState.AMBIGUOUS,
                observed_at=observed_at,
                error_class="MISSING_PROVIDER_HANDLE",
                message="submit returned without a durable operation handle",
                side_effect_may_have_occurred=True,
                retry_safe=False,
            )
        handle = ProviderTransportHandle(
            provider_key=self.provider_key,
            kind=ProviderHandleKind.OPERATION,
            handle_id=op_id,
            project_handle=self._runtime_project_id,
        )
        return ProviderTransportObservation(
            provider_key=self.provider_key,
            kind=ProviderObservationKind.SUBMIT,
            state=ProviderObservationState.ACCEPTED,
            observed_at=observed_at,
            handle=handle,
            side_effect_may_have_occurred=True,
            retry_safe=False,
        )

    async def poll(
        self, handle: ProviderTransportHandle, *, observed_at: datetime
    ) -> ProviderTransportObservation:
        return await self._poll(handle, observed_at=observed_at, kind=ProviderObservationKind.POLL)

    async def cancel(
        self, handle: ProviderTransportHandle, *, observed_at: datetime
    ) -> ProviderTransportObservation:
        return ProviderTransportObservation(
            provider_key=self.provider_key,
            kind=ProviderObservationKind.CANCEL,
            state=ProviderObservationState.UNSUPPORTED,
            observed_at=observed_at,
            handle=handle,
            message="current Flow transport has no proven cancel API",
            side_effect_may_have_occurred=False,
            retry_safe=False,
        )

    async def reconcile(
        self,
        handle: ProviderTransportHandle | None,
        *,
        observed_at: datetime,
    ) -> ProviderTransportObservation:
        if handle is None:
            return ProviderTransportObservation(
                provider_key=self.provider_key,
                kind=ProviderObservationKind.RECONCILE,
                state=ProviderObservationState.AMBIGUOUS,
                observed_at=observed_at,
                error_class="INSUFFICIENT_SUBMISSION_PROOF",
                message="cannot reconcile Flow submission without a durable provider handle",
                side_effect_may_have_occurred=True,
                retry_safe=False,
            )
        return await self._poll(handle, observed_at=observed_at, kind=ProviderObservationKind.RECONCILE)

    async def _poll(
        self,
        handle: ProviderTransportHandle,
        *,
        observed_at: datetime,
        kind: ProviderObservationKind,
    ) -> ProviderTransportObservation:
        if handle.provider_key != self.provider_key or handle.kind is not ProviderHandleKind.OPERATION:
            return ProviderTransportObservation(
                provider_key=self.provider_key,
                kind=kind,
                state=ProviderObservationState.AMBIGUOUS,
                observed_at=observed_at,
                handle=handle,
                error_class="HANDLE_PROVIDER_MISMATCH",
                message="operation handle does not belong to this Flow adapter",
                side_effect_may_have_occurred=True,
                retry_safe=False,
            )
        try:
            result = await self._client.check_video_status(
                [{"operation": {"name": handle.handle_id}}]
            )
        except Exception as exc:
            return ProviderTransportObservation(
                provider_key=self.provider_key,
                kind=kind,
                state=ProviderObservationState.AMBIGUOUS,
                observed_at=observed_at,
                handle=handle,
                error_class=type(exc).__name__,
                message=str(exc),
                side_effect_may_have_occurred=True,
                retry_safe=False,
            )
        return _normalize_operation_poll(
            provider_key=self.provider_key,
            result=result,
            handle=handle,
            observed_at=observed_at,
            kind=kind,
        )

    def _unsupported(
        self,
        plan: ProviderExecutionPlan,
        observed_at: datetime,
        message: str,
    ) -> ProviderTransportObservation:
        return ProviderTransportObservation(
            provider_key=self.provider_key,
            kind=ProviderObservationKind.SUBMIT,
            state=ProviderObservationState.UNSUPPORTED,
            observed_at=observed_at,
            message=message,
            side_effect_may_have_occurred=False,
            retry_safe=False,
        )

    def _ambiguous_submit(
        self, observed_at: datetime, exc: Exception
    ) -> ProviderTransportObservation:
        return ProviderTransportObservation(
            provider_key=self.provider_key,
            kind=ProviderObservationKind.SUBMIT,
            state=ProviderObservationState.AMBIGUOUS,
            observed_at=observed_at,
            error_class=type(exc).__name__,
            message=str(exc),
            side_effect_may_have_occurred=True,
            retry_safe=False,
        )


class OmniFlashProviderAdapter(ProviderAdapterPort):
    """Compatibility adapter over the live-captured Omni Flash surfaces."""

    def __init__(
        self,
        *,
        provider_key: str,
        runtime_project_id: str,
        supported_model_versions: frozenset[str],
        text_submit: Callable[..., Awaitable[dict]],
        first_submit: Callable[..., Awaitable[dict]],
        first_last_submit: Callable[..., Awaitable[dict]],
        references_submit: Callable[..., Awaitable[dict]],
        workflow_poll: Callable[..., Awaitable[dict]],
        operation_poll: Callable[[list[dict]], Awaitable[dict]],
    ) -> None:
        self.provider_key = str(provider_key).strip()
        self._runtime_project_id = str(runtime_project_id).strip()
        self._supported_model_versions = frozenset(
            str(value).strip() for value in supported_model_versions if str(value).strip()
        )
        self._text_submit = text_submit
        self._first_submit = first_submit
        self._first_last_submit = first_last_submit
        self._references_submit = references_submit
        self._workflow_poll = workflow_poll
        self._operation_poll = operation_poll
        if not self.provider_key or not self._runtime_project_id:
            raise ValueError("Omni adapter requires provider_key and runtime_project_id")
        if not self._supported_model_versions:
            raise ValueError("Omni adapter requires explicit supported_model_versions")

    @classmethod
    def from_current_services(
        cls,
        *,
        provider_key: str,
        runtime_project_id: str,
        supported_model_versions: frozenset[str],
    ) -> "OmniFlashProviderAdapter":
        from agent.services.flow_client import get_flow_client
        from agent.services.omni_flash import (
            check_omni_flash_status,
            generate_omni_flash_first_frame_video,
            generate_omni_flash_first_last_video,
            generate_omni_flash_text_video,
            generate_omni_flash_video,
        )

        return cls(
            provider_key=provider_key,
            supported_model_versions=supported_model_versions,
            runtime_project_id=runtime_project_id,
            text_submit=generate_omni_flash_text_video,
            first_submit=generate_omni_flash_first_frame_video,
            first_last_submit=generate_omni_flash_first_last_video,
            references_submit=generate_omni_flash_video,
            workflow_poll=check_omni_flash_status,
            operation_poll=get_flow_client().check_video_status,
        )

    async def submit(
        self, plan: ProviderExecutionPlan, *, observed_at: datetime
    ) -> ProviderTransportObservation:
        if plan.provider_key != self.provider_key:
            return self._unsupported(observed_at, "plan selected a different provider")
        if plan.model_version not in self._supported_model_versions:
            return self._unsupported(
                observed_at,
                f"selected ProviderProfile model_version {plan.model_version!r} is not bound to this Omni adapter dialect",
            )
        try:
            expected_model = _omni_transport_model_key(
                plan.mode,
                plan.duration_seconds,
                plan.resolution,
            )
            aspect = _aspect(plan.aspect_ratio)
        except ProviderAdapterUnsupported as exc:
            return self._unsupported(observed_at, str(exc))
        if plan.model_version != expected_model:
            return self._unsupported(
                observed_at,
                f"Omni transport would lower to {expected_model!r}, not selected model {plan.model_version!r}",
            )
        try:
            common = dict(
                prompt=plan.prompt,
                project_id=self._runtime_project_id,
                scene_id=plan.shot_ir_ref.logical_id.root,
                duration_s=plan.duration_seconds,
                resolution=plan.resolution,
                aspect_ratio=aspect,
            )
            if plan.mode is ProviderExecutionMode.TEXT_TO_VIDEO:
                if plan.runtime_references:
                    return self._unsupported(observed_at, "text-to-video cannot silently discard references")
                result = await self._text_submit(**common)
            elif plan.mode is ProviderExecutionMode.FIRST_FRAME_TO_VIDEO:
                if len(plan.runtime_references) != 1:
                    return self._unsupported(observed_at, "first-frame mode requires exactly one reference")
                result = await self._first_submit(
                    start_image_media_id=plan.runtime_references[0].media_id,
                    **common,
                )
            elif plan.mode is ProviderExecutionMode.FIRST_LAST_FRAME_TO_VIDEO:
                if len(plan.runtime_references) != 2:
                    return self._unsupported(observed_at, "first+last mode requires exactly two references")
                start_roles = {"frame.start", "start_frame", "first_frame", "video.start_frame"}
                end_roles = {"frame.end", "end_frame", "last_frame", "video.end_frame"}
                start_refs = [
                    item for item in plan.runtime_references if item.role.strip().lower() in start_roles
                ]
                end_refs = [
                    item for item in plan.runtime_references if item.role.strip().lower() in end_roles
                ]
                if len(start_refs) != 1 or len(end_refs) != 1:
                    return self._unsupported(
                        observed_at,
                        "first+last mode requires explicit runtime start/end reference roles",
                    )
                result = await self._first_last_submit(
                    start_image_media_id=start_refs[0].media_id,
                    end_image_media_id=end_refs[0].media_id,
                    **common,
                )
            elif plan.mode is ProviderExecutionMode.REFERENCES_TO_VIDEO:
                if not plan.runtime_references:
                    return self._unsupported(observed_at, "references-to-video requires at least one reference")
                result = await self._references_submit(
                    reference_media_ids=[item.media_id for item in plan.runtime_references],
                    **common,
                )
            else:  # pragma: no cover - enum exhaustiveness
                return self._unsupported(observed_at, f"unsupported execution mode {plan.mode.value}")
        except ProviderAdapterUnsupported as exc:
            return self._unsupported(observed_at, str(exc))
        except Exception as exc:
            return self._ambiguous_submit(observed_at, exc)

        error = _error_text(result)
        if error:
            return ProviderTransportObservation(
                provider_key=self.provider_key,
                kind=ProviderObservationKind.SUBMIT,
                state=ProviderObservationState.AMBIGUOUS,
                observed_at=observed_at,
                error_class="SUBMIT_RESULT_ERROR",
                message=error,
                side_effect_may_have_occurred=True,
                retry_safe=False,
            )

        data = result.get("data") if isinstance(result, dict) and isinstance(result.get("data"), dict) else {}
        workflows = data.get("workflows") if isinstance(data, dict) else None
        if isinstance(workflows, list) and workflows:
            workflow = workflows[0] if isinstance(workflows[0], dict) else {}
            workflow_id = workflow.get("name")
            media_id = workflow.get("primary_media_id") or workflow.get("primaryMediaId")
            if workflow_id and media_id:
                handle = ProviderTransportHandle(
                    provider_key=self.provider_key,
                    kind=ProviderHandleKind.WORKFLOW,
                    handle_id=str(workflow_id),
                    project_handle=str(workflow.get("project_id") or self._runtime_project_id),
                    primary_media_id=str(media_id),
                )
                return ProviderTransportObservation(
                    provider_key=self.provider_key,
                    kind=ProviderObservationKind.SUBMIT,
                    state=ProviderObservationState.ACCEPTED,
                    observed_at=observed_at,
                    handle=handle,
                    side_effect_may_have_occurred=True,
                    retry_safe=False,
                )

        operation = _first_operation(result if isinstance(result, dict) else {})
        op_id = _operation_id(operation)
        if op_id:
            handle = ProviderTransportHandle(
                provider_key=self.provider_key,
                kind=ProviderHandleKind.OPERATION,
                handle_id=op_id,
                project_handle=self._runtime_project_id,
            )
            return ProviderTransportObservation(
                provider_key=self.provider_key,
                kind=ProviderObservationKind.SUBMIT,
                state=ProviderObservationState.ACCEPTED,
                observed_at=observed_at,
                handle=handle,
                side_effect_may_have_occurred=True,
                retry_safe=False,
            )
        return ProviderTransportObservation(
            provider_key=self.provider_key,
            kind=ProviderObservationKind.SUBMIT,
            state=ProviderObservationState.AMBIGUOUS,
            observed_at=observed_at,
            error_class="MISSING_PROVIDER_HANDLE",
            message="Omni submit returned without workflow/operation proof",
            side_effect_may_have_occurred=True,
            retry_safe=False,
        )

    async def poll(
        self, handle: ProviderTransportHandle, *, observed_at: datetime
    ) -> ProviderTransportObservation:
        return await self._poll(handle, observed_at=observed_at, kind=ProviderObservationKind.POLL)

    async def cancel(
        self, handle: ProviderTransportHandle, *, observed_at: datetime
    ) -> ProviderTransportObservation:
        return ProviderTransportObservation(
            provider_key=self.provider_key,
            kind=ProviderObservationKind.CANCEL,
            state=ProviderObservationState.UNSUPPORTED,
            observed_at=observed_at,
            handle=handle,
            message="current Omni transport has no proven cancel API",
            side_effect_may_have_occurred=False,
            retry_safe=False,
        )

    async def reconcile(
        self,
        handle: ProviderTransportHandle | None,
        *,
        observed_at: datetime,
    ) -> ProviderTransportObservation:
        if handle is None:
            return ProviderTransportObservation(
                provider_key=self.provider_key,
                kind=ProviderObservationKind.RECONCILE,
                state=ProviderObservationState.AMBIGUOUS,
                observed_at=observed_at,
                error_class="INSUFFICIENT_SUBMISSION_PROOF",
                message="reconcile never resubmits and no durable provider handle was supplied",
                side_effect_may_have_occurred=True,
                retry_safe=False,
            )
        return await self._poll(handle, observed_at=observed_at, kind=ProviderObservationKind.RECONCILE)

    async def _poll(
        self,
        handle: ProviderTransportHandle,
        *,
        observed_at: datetime,
        kind: ProviderObservationKind,
    ) -> ProviderTransportObservation:
        if handle.provider_key != self.provider_key:
            return ProviderTransportObservation(
                provider_key=self.provider_key,
                kind=kind,
                state=ProviderObservationState.AMBIGUOUS,
                observed_at=observed_at,
                handle=handle,
                error_class="HANDLE_PROVIDER_MISMATCH",
                message="handle does not belong to this Omni adapter",
                side_effect_may_have_occurred=True,
                retry_safe=False,
            )
        try:
            if handle.kind is ProviderHandleKind.WORKFLOW:
                if not handle.primary_media_id:
                    raise ValueError("workflow handle missing primary_media_id")
                result = await self._workflow_poll(
                    [{
                        "name": handle.handle_id,
                        "primary_media_id": handle.primary_media_id,
                        "project_id": handle.project_handle or self._runtime_project_id,
                    }],
                    False,
                    handle.project_handle or self._runtime_project_id,
                )
                workflows = result.get("workflows") if isinstance(result, dict) else None
                item = workflows[0] if isinstance(workflows, list) and workflows else None
                if isinstance(item, dict) and item.get("done"):
                    media = item.get("media") if isinstance(item.get("media"), dict) else {}
                    return ProviderTransportObservation(
                        provider_key=self.provider_key,
                        kind=kind,
                        state=ProviderObservationState.SUCCEEDED,
                        observed_at=observed_at,
                        handle=handle,
                        output_media_id=str(media.get("media_id") or handle.primary_media_id),
                        output_url=str(media.get("url")) if media.get("url") else None,
                        retry_safe=False,
                    )
                if isinstance(item, dict):
                    return ProviderTransportObservation(
                        provider_key=self.provider_key,
                        kind=kind,
                        state=ProviderObservationState.PENDING,
                        observed_at=observed_at,
                        handle=handle,
                        side_effect_may_have_occurred=True,
                        retry_safe=False,
                    )
                raise ValueError("workflow poll returned no recognizable workflow")

            result = await self._operation_poll([{"operation": {"name": handle.handle_id}}])
            return _normalize_operation_poll(
                provider_key=self.provider_key,
                result=result,
                handle=handle,
                observed_at=observed_at,
                kind=kind,
            )
        except Exception as exc:
            return ProviderTransportObservation(
                provider_key=self.provider_key,
                kind=kind,
                state=ProviderObservationState.AMBIGUOUS,
                observed_at=observed_at,
                handle=handle,
                error_class=type(exc).__name__,
                message=str(exc),
                side_effect_may_have_occurred=True,
                retry_safe=False,
            )

    def _unsupported(self, observed_at: datetime, message: str) -> ProviderTransportObservation:
        return ProviderTransportObservation(
            provider_key=self.provider_key,
            kind=ProviderObservationKind.SUBMIT,
            state=ProviderObservationState.UNSUPPORTED,
            observed_at=observed_at,
            message=message,
            side_effect_may_have_occurred=False,
            retry_safe=False,
        )

    def _ambiguous_submit(
        self, observed_at: datetime, exc: Exception
    ) -> ProviderTransportObservation:
        return ProviderTransportObservation(
            provider_key=self.provider_key,
            kind=ProviderObservationKind.SUBMIT,
            state=ProviderObservationState.AMBIGUOUS,
            observed_at=observed_at,
            error_class=type(exc).__name__,
            message=str(exc),
            side_effect_may_have_occurred=True,
            retry_safe=False,
        )
