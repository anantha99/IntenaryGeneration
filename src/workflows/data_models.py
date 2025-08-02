"""
Data models for the Travel Itinerary Workflow.

Contains the main response structures and metadata for orchestrating
the sequential execution of all travel planning agents.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

# Import existing agent data models
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.request_parser import CoreTravelRequest
from agents.activities_planner import ItineraryOutput
from agents.accommodation_suggester import AccommodationOutput


class WorkflowStage(Enum):
    """Enum for workflow stages"""
    PARSING_REQUEST = "parsing_request"
    FINDING_PLACES = "finding_places" 
    PLANNING_ACTIVITIES = "planning_activities"
    FINDING_ACCOMMODATIONS = "finding_accommodations"
    ASSEMBLING_RESPONSE = "assembling_response"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentStatus(Enum):
    """Enum for individual agent status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class AgentExecution:
    """Metadata for individual agent execution"""
    agent_name: str
    status: AgentStatus = AgentStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    
    def start(self):
        """Mark agent as started"""
        self.status = AgentStatus.RUNNING
        self.start_time = time.time()
    
    def complete(self):
        """Mark agent as completed"""
        self.status = AgentStatus.COMPLETED
        self.end_time = time.time()
        if self.start_time:
            self.duration = self.end_time - self.start_time
    
    def fail(self, error_message: str):
        """Mark agent as failed"""
        self.status = AgentStatus.FAILED
        self.end_time = time.time()
        if self.start_time:
            self.duration = self.end_time - self.start_time
        self.error_message = error_message
    
    def skip(self, reason: str):
        """Mark agent as skipped"""
        self.status = AgentStatus.SKIPPED
        self.error_message = reason


@dataclass
class WorkflowMetadata:
    """Metadata for the entire workflow execution"""
    workflow_id: str
    total_start_time: float
    total_end_time: Optional[float] = None
    total_duration: Optional[float] = None
    current_stage: WorkflowStage = WorkflowStage.PARSING_REQUEST
    overall_status: str = "running"
    
    # Agent execution tracking
    request_parser: AgentExecution = field(default_factory=lambda: AgentExecution("RequestParser"))
    activities_planner: AgentExecution = field(default_factory=lambda: AgentExecution("ActivitiesPlanner"))
    accommodation_suggester: AgentExecution = field(default_factory=lambda: AgentExecution("AccommodationSuggester"))
    
    # Error and warning tracking
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Performance metrics
    performance_notes: List[str] = field(default_factory=list)
    
    def complete_workflow(self):
        """Mark the entire workflow as completed"""
        self.total_end_time = time.time()
        self.total_duration = self.total_end_time - self.total_start_time
        self.current_stage = WorkflowStage.COMPLETED
        self.overall_status = "completed"
    
    def fail_workflow(self, error_message: str):
        """Mark the entire workflow as failed"""
        self.total_end_time = time.time()
        self.total_duration = self.total_end_time - self.total_start_time
        self.current_stage = WorkflowStage.FAILED
        self.overall_status = "failed"
        self.errors.append(f"Workflow failure: {error_message}")
    
    def get_completion_percentage(self) -> float:
        """Calculate overall completion percentage"""
        completed_agents = sum(1 for agent in [self.request_parser, self.activities_planner, self.accommodation_suggester] 
                             if agent.status == AgentStatus.COMPLETED)
        return (completed_agents / 3) * 100
    
    def get_current_agent(self) -> Optional[AgentExecution]:
        """Get the currently running agent"""
        for agent in [self.request_parser, self.activities_planner, self.accommodation_suggester]:
            if agent.status == AgentStatus.RUNNING:
                return agent
        return None
    
    def has_errors(self) -> bool:
        """Check if any errors occurred"""
        return len(self.errors) > 0 or any(agent.status == AgentStatus.FAILED 
                                          for agent in [self.request_parser, self.activities_planner, self.accommodation_suggester])
    
    def is_partial_success(self) -> bool:
        """Check if we have partial success (some agents completed, some failed)"""
        statuses = [self.request_parser.status, self.activities_planner.status, self.accommodation_suggester.status]
        has_completed = any(status == AgentStatus.COMPLETED for status in statuses)
        has_failed = any(status == AgentStatus.FAILED for status in statuses)
        return has_completed and has_failed


@dataclass
class TravelItineraryResponse:
    """
    Complete response from the Travel Itinerary Workflow.
    
    Contains all outputs from individual agents plus workflow metadata.
    """
    # Core data from agents
    parsed_request: Optional[CoreTravelRequest] = None
    itinerary: Optional[ItineraryOutput] = None
    accommodations: Optional[AccommodationOutput] = None
    
    # Workflow metadata
    workflow_metadata: Optional[WorkflowMetadata] = None
    
    # Human-readable summary
    summary: Optional[str] = None
    
    # Original user input
    user_input: Optional[str] = None
    
    def is_complete(self) -> bool:
        """Check if we have a complete response"""
        return (self.parsed_request is not None and 
                self.itinerary is not None and 
                self.accommodations is not None)
    
    def is_partial(self) -> bool:
        """Check if we have partial results"""
        components = [self.parsed_request, self.itinerary, self.accommodations]
        has_some = any(comp is not None for comp in components)
        has_all = all(comp is not None for comp in components)
        return has_some and not has_all
    
    def get_completion_status(self) -> str:
        """Get human-readable completion status"""
        if self.is_complete():
            return "Complete itinerary generated successfully"
        elif self.is_partial():
            components = []
            if self.parsed_request: components.append("request parsing")
            if self.itinerary: components.append("activity planning")
            if self.accommodations: components.append("accommodation suggestions")
            return f"Partial results: {', '.join(components)}"
        else:
            return "No results generated"
    
    def get_available_data(self) -> Dict[str, Any]:
        """Get all available data as a dictionary"""
        data = {}
        
        if self.parsed_request:
            data["parsed_request"] = self.parsed_request
        
        if self.itinerary:
            data["itinerary"] = self.itinerary
        
        if self.accommodations:
            data["accommodations"] = self.accommodations
        
        if self.workflow_metadata:
            data["workflow_metadata"] = self.workflow_metadata
        
        if self.summary:
            data["summary"] = self.summary
        
        if self.user_input:
            data["user_input"] = self.user_input
        
        return data
    
    def get_error_summary(self) -> List[str]:
        """Get summary of all errors"""
        errors = []
        
        if self.workflow_metadata:
            errors.extend(self.workflow_metadata.errors)
            
            # Add agent-specific errors
            for agent in [self.workflow_metadata.request_parser, 
                         self.workflow_metadata.activities_planner, 
                         self.workflow_metadata.accommodation_suggester]:
                if agent.status == AgentStatus.FAILED and agent.error_message:
                    errors.append(f"{agent.agent_name}: {agent.error_message}")
        
        return errors


# Helper functions for response creation
def create_workflow_metadata(workflow_id: str) -> WorkflowMetadata:
    """Create new workflow metadata with current timestamp"""
    return WorkflowMetadata(
        workflow_id=workflow_id,
        total_start_time=time.time()
    )


def create_empty_response(user_input: str, workflow_metadata: WorkflowMetadata) -> TravelItineraryResponse:
    """Create an empty response with basic metadata"""
    return TravelItineraryResponse(
        user_input=user_input,
        workflow_metadata=workflow_metadata
    )