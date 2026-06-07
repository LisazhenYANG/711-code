from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LocationInput(BaseModel):
    city: str = "上海"
    area: str = "静安区"
    mode: str | None = None


class RouteGenerateRequest(BaseModel):
    location: LocationInput = Field(default_factory=LocationInput)
    time_slot: str = "下午"
    people: str = "2人"
    moods: list[str] = Field(default_factory=list)
    discover_items: list[str] = Field(default_factory=list)
    user_profile: dict[str, Any] = Field(default_factory=dict)


class ProductSelection(BaseModel):
    name: str
    price: str = ""


class BookingCheckoutItem(BaseModel):
    name: str
    category: str = ""
    booking_type: str = Field("", alias="bookingType")
    time: str = "待定"
    selected_product: ProductSelection | None = Field(
        None, alias="selectedProduct"
    )
    paid: bool = False

    model_config = {"populate_by_name": True}


class BookingCheckoutRequest(BaseModel):
    trip_id: str | None = None
    items: list[BookingCheckoutItem] = Field(default_factory=list)


class TripCreateRequest(BaseModel):
    title: str = "今日路线"
    city: str = "上海"
    date: str = "今天"
    route: list[dict[str, Any]] = Field(default_factory=list)
    weather: dict[str, Any] | None = None
    outfit: dict[str, Any] | None = None
    booking_checklist: list[dict[str, Any]] = Field(
        default_factory=list, alias="bookingChecklist"
    )
    booking_results: list[dict[str, Any]] = Field(
        default_factory=list, alias="bookingResults"
    )
    packing_list: list[str] = Field(default_factory=list, alias="packingList")
    chat_history: list[dict[str, Any]] = Field(
        default_factory=list, alias="chatHistory"
    )

    model_config = {"populate_by_name": True}


class FeedbackRequest(BaseModel):
    trip_id: str | None = None
    route_id: str | None = None
    rating: int | None = Field(None, ge=1, le=5)
    deleted_poi_ids: list[str] = Field(default_factory=list)
    notes: str = ""


class IntentInput(BaseModel):
    origin_lat: float
    origin_lng: float
    origin_name: str = "当前位置"
    time_slot: str = "下午"
    people_count: int = Field(2, ge=1, le=20)
    transport_mode: str = "transit"
    moods: list[str] = Field(default_factory=list)
    sub_categories: list[str] = Field(default_factory=list)
    free_text: str = ""
    budget_per_person: float | None = None
    locked_poi_ids: list[str] = Field(default_factory=list)
    health_constraints: list[str] = Field(default_factory=list)
    city_code: str = "021"


class AiPlanRequest(BaseModel):
    user_id: str = "anon"
    intent: IntentInput
    weather: dict[str, Any] | None = None


class AiFeedbackRequest(BaseModel):
    user_id: str
    intent: dict[str, Any] | None = None
    top_routes: list[dict[str, Any]] = Field(default_factory=list)
    debate_transcript: list[dict[str, Any]] = Field(default_factory=list)
    user_choice_route_id: str | None = None
    user_deleted_poi_ids: list[str] = Field(default_factory=list)
    user_rating: int | None = Field(None, ge=1, le=5)


class QueueTicketRequest(BaseModel):
    restaurant_id: str
    user_id: str
    people_count: int = Field(2, ge=1, le=20)


class ReservationRequest(BaseModel):
    restaurant_id: str
    user_id: str
    people_count: int = Field(2, ge=1, le=20)
    reserve_for_time: str
    special_requests: str = ""


class RouteActionRequest(BaseModel):
    action: str
    route: list[dict[str, Any]] = Field(default_factory=list)
    locked_indexes: list[int] = Field(default_factory=list, alias="lockedIndexes")
    hidden_indexes: list[int] = Field(default_factory=list, alias="hiddenIndexes")
    index: int | None = None
    value: str = ""
    recommendation_index: int | None = Field(None, alias="recommendationIndex")
    priorities: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}
