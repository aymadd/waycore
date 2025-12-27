# Phase 15 Manual Testing Guide

This document provides test questions and expected behaviors for manually
testing Phase 15 AI features.

## Prerequisites

1. All Docker containers running: `docker compose -f docker/compose/dev.yml ps`
2. QML UI running: `poetry run python -m device.apps.ui.main`
3. Navigate to AI Assistant app in the UI

---

## 1. Sensor Data (MCP Sensors)

These questions test the AI's ability to read device sensor data via MCP tools.

### Temperature

| Question                                | Expected Behavior                                  |
| --------------------------------------- | -------------------------------------------------- |
| "What's the current temperature?"       | Returns temperature in Celsius (e.g., "22.5°C")    |
| "What's the temperature in Fahrenheit?" | Returns temperature in Fahrenheit (e.g., "72.5°F") |

### Location & Navigation

| Question                      | Expected Behavior                             |
| ----------------------------- | --------------------------------------------- |
| "Where am I?"                 | Returns GPS coordinates (latitude, longitude) |
| "What's my current location?" | Returns GPS with accuracy and elevation       |
| "What direction am I facing?" | Returns compass heading (e.g., "45° NE")      |
| "What's my altitude?"         | Returns elevation in meters/feet              |

### Device Status

| Question                           | Expected Behavior                              |
| ---------------------------------- | ---------------------------------------------- |
| "What's the battery level?"        | Returns battery percentage and charging status |
| "How much battery do I have left?" | Returns battery level with time estimate       |
| "What time is it?"                 | Returns current device time and timezone       |

### Combined Queries

| Question                               | Expected Behavior                          |
| -------------------------------------- | ------------------------------------------ |
| "Give me all sensor readings"          | Returns temperature, GPS, compass, battery |
| "What are current weather conditions?" | Returns temperature, pressure, altitude    |

---

## 2. Device Actions (MCP Actions)

These questions test the AI's ability to perform device actions.

### Notes App

| Question                                   | Expected Behavior                        |
| ------------------------------------------ | ---------------------------------------- |
| "Create a note saying 'Test note from AI'" | Creates a new note, returns confirmation |
| "What notes do I have?"                    | Lists existing notes with titles         |
| "Show me my notes"                         | Lists notes with summaries               |

### Mesh Network (if mesh is active)

| Question                                | Expected Behavior                           |
| --------------------------------------- | ------------------------------------------- |
| "Who is on the mesh network?"           | Lists connected nodes                       |
| "Send a message to all: Hello everyone" | Requests confirmation, then sends broadcast |

---

## 3. Software Documentation (RAG Docs)

These questions test the AI's ability to search Waycore software documentation.

| Question                           | Expected Behavior                                               |
| ---------------------------------- | --------------------------------------------------------------- |
| "How do I use the compass app?"    | Explains compass calibration, features                          |
| "What apps are available?"         | Lists Home, Compass, Notes, Mesh, Camera, Gallery, AI, Settings |
| "How do I calibrate the compass?"  | Step-by-step calibration instructions                           |
| "How do I create a note?"          | Instructions for Notes app                                      |
| "What are the keyboard shortcuts?" | Lists available shortcuts                                       |
| "How do I send a mesh message?"    | Explains mesh messaging features                                |

---

## 4. Outdoor Survival Knowledge (RAG Outdoor)

These questions test the AI's survival/outdoor knowledge base.

### Fire & Shelter

| Question                                 | Expected Behavior                              |
| ---------------------------------------- | ---------------------------------------------- |
| "How do I start a fire without matches?" | Fire-starting techniques, safety warnings      |
| "What are fire-starting methods?"        | Friction, flint/steel, solar, chemical methods |
| "How do I build an emergency shelter?"   | Shelter construction techniques                |

### Water & Survival

| Question                                 | Expected Behavior                       |
| ---------------------------------------- | --------------------------------------- |
| "How do I purify water in the wild?"     | Boiling, filtration, chemical treatment |
| "What are signs of dehydration?"         | Symptoms and treatment                  |
| "How do I find water in the wilderness?" | Water sources, indicators               |

### First Aid

| Question                            | Expected Behavior                          |
| ----------------------------------- | ------------------------------------------ |
| "How do I treat a snake bite?"      | First aid steps with DANGER safety warning |
| "What should I do for hypothermia?" | Symptoms, treatment, warming techniques    |
| "How do I treat a blister?"         | Blister care instructions                  |

### Navigation

| Question                                 | Expected Behavior                  |
| ---------------------------------------- | ---------------------------------- |
| "How do I find north without a compass?" | Sun, stars, natural indicators     |
| "How do I use the stars to navigate?"    | Polaris, Southern Cross navigation |
| "How do I read a topographic map?"       | Contour lines, symbols explanation |

### Knots

| Question                               | Expected Behavior                |
| -------------------------------------- | -------------------------------- |
| "How do I tie a bowline knot?"         | Step-by-step knot instructions   |
| "What knot should I use for climbing?" | Appropriate knot recommendations |
| "What are essential survival knots?"   | List of key knots with uses      |

### Plants & Foraging

| Question                           | Expected Behavior                       |
| ---------------------------------- | --------------------------------------- |
| "Is wild mint safe to eat?"        | Edibility info with CAUTION level       |
| "How do I identify edible plants?" | Identification tips with DANGER warning |
| "What plants should I avoid?"      | Toxic plant identification              |

### Weather

| Question                                | Expected Behavior                  |
| --------------------------------------- | ---------------------------------- |
| "What clouds indicate rain?"            | Cloud types and weather prediction |
| "How do I predict weather in the wild?" | Natural weather signs              |

---

## 5. General Conversation

These test the AI's conversational abilities without tools.

| Question                     | Expected Behavior                                       |
| ---------------------------- | ------------------------------------------------------- |
| "Hello, who are you?"        | Introduces itself as Waycore AI assistant               |
| "What can you help me with?" | Lists capabilities (sensors, notes, survival knowledge) |
| "Tell me a joke"             | Provides a joke (general LLM capability)                |

---

## Troubleshooting

### If sensors don't work:

1. Check core-daemon is healthy: `curl http://localhost:8000/health`
2. Check environment vars:
   `docker exec waycore-ai-service env | grep CORE_DAEMON`
3. Test API directly: `curl http://localhost:8000/api/system/temperature`

### If notes don't work:

1. Check data-logger is healthy: `curl http://localhost:8002/health`
2. Test API directly: `curl http://localhost:8002/api/notes`

### If RAG doesn't return results:

1. Check knowledge base exists: `ls -la data/outdoor/`
2. Verify container mount:
   `docker exec waycore-ai-service ls /app/data/outdoor/`

### If responses are slow:

This is expected - Phi-3 Mini runs on CPU. Responses typically take 5-15
seconds. To speed up: Switch to TinyLlama model or reduce `max_tokens` in
phi3_runner.py.

---

## Expected Response Patterns

### Safety Levels in Survival Answers

The AI should include safety warnings for dangerous topics:

- **SAFE**: General information
- **CAUTION**: Requires care (foraging, fire)
- **WARNING**: Risk of injury (first aid, knots)
- **DANGER**: Serious risk (plant identification, snake bites)
- **LETHAL**: Life-threatening if done wrong

### Sources

Survival answers should cite sources:

- "Based on FM21-76 Survival Manual..."
- "According to the Ranger Handbook..."
- "Source: BSA Wilderness First Aid Guide..."

---

_Last updated: 2025-12-27_
