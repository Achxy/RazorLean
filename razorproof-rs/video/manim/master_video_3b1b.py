# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

"""Manim entrypoint; chapter implementations live in razorproof_video/scenes."""

from razorproof_video.scenes.boundary_failures import BoundaryFailures as _BoundaryFailures
from razorproof_video.scenes.failure_chains import FailureChains as _FailureChains
from razorproof_video.scenes.final_proof import FinalProof as _FinalProof
from razorproof_video.scenes.invariant_scanner import InvariantScanner as _InvariantScanner
from razorproof_video.scenes.lost_coordinate import LostCoordinate as _LostCoordinate
from razorproof_video.scenes.opening_proof import OpeningProof as _OpeningProof
from razorproof_video.scenes.provider_evidence import ProviderEvidence as _ProviderEvidence
from razorproof_video.scenes.semantic_firewall import SemanticFirewall as _SemanticFirewall


# Manim discovers classes defined in the entry module. These deliberately empty
# adapters keep the command line stable while every chapter stays independently
# editable and testable.
class OpeningProof(_OpeningProof):
    pass


class LostCoordinate(_LostCoordinate):
    pass


class InvariantScanner(_InvariantScanner):
    pass


class BoundaryFailures(_BoundaryFailures):
    pass


class FailureChains(_FailureChains):
    pass


class SemanticFirewall(_SemanticFirewall):
    pass


class ProviderEvidence(_ProviderEvidence):
    pass


class FinalProof(_FinalProof):
    pass


SCENES = [
    OpeningProof,
    LostCoordinate,
    InvariantScanner,
    BoundaryFailures,
    FailureChains,
    SemanticFirewall,
    ProviderEvidence,
    FinalProof,
]
