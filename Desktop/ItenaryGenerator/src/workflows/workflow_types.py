"""
Data types and schemas for the Travel Itinerary Workflow

Defines the output schemas and data structures for the parallel workflow execution.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

# Import existing agent output types
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from agents.request_parser import CoreTravelRequest
    from agents.activities_planner import ItineraryOutput
    from agents.accommodation_suggester import AccommodationOutput
except ImportError:
    # Handle import errors gracefully during development
    CoreTravelRequest = None
    ItineraryOutput = None
    AccommodationOutput = None


@dataclass
class TravelItineraryResponse:
    """Complete travel itinerary response from parallel workflow execution"""
    
    # Core data
    request_summary: Dict  # CoreTravelRequest as dict
    itinerary: ItineraryOutput
    accommodations: AccommodationOutput
    
    # Metadata
    final_cost_estimate: Optional[str] = None
    generated_at: str = None
    processing_time: float = 0.0
    workflow_id: str = None
    
    # Error handling
    success: bool = True
    errors: Optional[List[str]] = None
    partial_results: bool = False
    
    def __post_init__(self):
        """Set generated_at if not provided"""
        if self.generated_at is None:
            self.generated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary with proper serialization"""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, default=str)


@dataclass
class WorkflowMetrics:
    """Performance metrics for workflow execution"""
    
    workflow_id: str
    total_time: float = 0.0
    parsing_time: float = 0.0
    parallel_time: float = 0.0
    activities_time: float = 0.0
    accommodation_time: float = 0.0
    assembly_time: float = 0.0
    
    def parallel_efficiency(self) -> float:
        """Calculate parallel execution efficiency percentage"""
        if self.parallel_time == 0:
            return 0.0
        
        max_agent_time = max(self.activities_time, self.accommodation_time)
        return (max_agent_time / self.parallel_time) * 100
    
    def get_summary(self) -> Dict:
        """Get metrics summary as dictionary"""
        return {
            'workflow_id': self.workflow_id,
            'total_time': round(self.total_time, 2),
            'parsing_time': round(self.parsing_time, 2),
            'parallel_time': round(self.parallel_time, 2),
            'activities_time': round(self.activities_time, 2),
            'accommodation_time': round(self.accommodation_time, 2),
            'assembly_time': round(self.assembly_time, 2),
            'parallel_efficiency': round(self.parallel_efficiency(), 1),
            'performance_target_met': self.total_time < 30.0,
            'parallel_target_met': self.parallel_time < 20.0
        }


class WorkflowException(Exception):
    """Base exception for workflow errors"""
    pass


class IncompleteRequestException(WorkflowException):
    """Request parsing needs more information"""
    
    def __init__(self, next_question: str, partial_data: Dict):
        self.next_question = next_question
        self.partial_data = partial_data
        super().__init__(f"Incomplete request: {next_question}")


class ActivitiesPlanningException(WorkflowException):
    """Activities planning failed"""
    pass


class AccommodationSearchException(WorkflowException):
    """Accommodation search failed"""
    pass


class ParallelExecutionException(WorkflowException):
    """Parallel execution encountered errors"""
    
    def __init__(self, activities_error: Optional[Exception] = None, 
                 accommodation_error: Optional[Exception] = None):
        self.activities_error = activities_error
        self.accommodation_error = accommodation_error
        
        errors = []
        if activities_error:
            errors.append(f"Activities: {activities_error}")
        if accommodation_error:
            errors.append(f"Accommodations: {accommodation_error}")
        
        super().__init__(f"Parallel execution failed: {'; '.join(errors)}")