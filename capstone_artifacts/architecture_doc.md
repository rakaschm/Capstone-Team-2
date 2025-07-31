# Architecture Document: Vacation Rental Recommendation MVP

---

## 1. Overview

This system is a web-based vacation rental recommendation platform designed to help travelers easily discover and reserve rental properties near their preferred activities and attractions. By connecting user interests directly to property recommendations, the platform streamlines the vacation planning experience.

**Primary User Personas:**
- **Travelers**: Individuals or families searching for vacation rentals based on proximity to specific attractions or activities.

**Key Business Goals:**
- Increase rental conversions by offering highly relevant recommendations.
- Provide a seamless and intuitive booking experience.
- Reduce user effort in planning and cross-referencing accommodations.

**Constraints & Assumptions:**
- **Technology Stack**: React + Tailwind CSS (Frontend), FastAPI (Python, Backend), SQLite (Database).
- **Budget/Timeline**: MVP scope; limited to web platform and core flows. No payment processing or user accounts.
- **Assumptions**: Users are not required to register. All data interactions are session-based or via simple user identification.

---

## 2. User Interface

### Main UI Components & Flows

- **Interest Selection Form**: Allows users to input a list of desired activities or attractions (e.g., "hiking," "museums," "beach").
- **Recommended Properties List**: Displays rental properties ranked by proximity and relevance to selected interests, with summary cards (name, location, price/night, distance to interests, amenities).
- **Property Details View**: Modal or page showing comprehensive details (photos, address, map, amenities, nearby activities, price).
- **Reservation Form**: Collects check-in/check-out dates; allows users to confirm reservation.
- **Confirmation Screen/Modal**: Shows reservation success and details.

### Technologies

- **Frontend Framework**: React (function components, hooks)
- **Styling**: Tailwind CSS for rapid, responsive UI development
- **Map Integration**: Embed map (e.g., Google Maps/Leaflet) to visualize property and activity locations (MVP may use static maps or remove if out-of-scope)
- **Interaction Patterns**:
  - Responsive layouts for mobile/tablet/desktop
  - Accessible forms (ARIA roles, keyboard navigation)
  - Use of modals for details and confirmations
  - Client-side form validation and error handling

---

## 3. Backend Services

### API Endpoints & Responsibilities

- **User Interests**
  - `POST /api/interests`: Accept user’s activities/attractions (session-based, no login)
- **Property Recommendations**
  - `POST /api/recommendations`: Given user interests, return ranked list of properties with distances and relevance scores
- **Property Details**
  - `GET /api/properties/{property_id}`: Fetch full details for a property
- **Reservations**
  - `POST /api/reservations`: Create a reservation with user info, property, and dates
  - `GET /api/reservations/{reservation_id}`: Retrieve reservation confirmation/details

### Service Implementation

- **Framework**: FastAPI (Python; async endpoints for scalability)
- **Modularity**: Separate routers/modules for interests, properties, reservations, and recommendations
- **Request Routing**: RESTful, versioned API endpoints
- **Data Validation**: Pydantic models for strict input/output data contracts
- **Async Processing**: Asynchronous DB queries and LLM calls to avoid blocking
- **Error Handling**: Standardized error responses (e.g., 422 for validation, 404 for missing property)
- **Security**: Minimal, as user accounts are out-of-scope; basic input sanitization

---

## 4. Database Design

### Schema Structure

- **Users**
  - Stores basic user info and a comma-separated list of interests (activities/attractions)
- **Properties**
  - Rental property data: name, address, price, amenities (comma-separated)
- **Reservations**
  - Tracks reservations linking user, property, and booking dates

#### Relationships

- **One-to-Many**: Users → Reservations
- **One-to-Many**: Properties → Reservations

#### Constraints

- **Foreign Keys**: Enforced between Reservations and Users/Properties
- **Unique**: User email (if collected, though registration is out-of-scope)
- **Indexes**: Primary keys by default; consider additional indexes on city, price for future scaling

#### SQLite Considerations

- **Concurrency**: SQLite is file-based; suitable for MVP and light traffic, but not for heavy concurrent usage
- **Full-Text Search**: Not available by default; basic LIKE queries on interests/amenities
- **Scalability**: Simple migration to PostgreSQL or similar when scaling is needed

---

## 5. Property Recommendation Engine

### User Interest Capture

- Users submit a free-form (comma-separated) list of activities or attractions.
- Captured via frontend form, stored as text in the Users table (no login required).

### Recommendation Process

- **Input:** List of user interests (e.g., "kayaking, art museums, food tours")
- **Process:**
  - Query Properties from the database.
  - Use an LLM (Large Language Model) to match and rank properties based on:
    - Proximity to described activities/attractions (using address/city as proxy)
    - Similarity of property amenities to activity needs
    - Any explicit mention of activities/attractions in property data
  - LLM prompt includes user interests and property dataset excerpt.
  - LLM returns a ranked (scored) list of property IDs with reasoning.

