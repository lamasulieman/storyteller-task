# Storyteller CLI Tool

The Storyteller CLI tool provides an interface for converting sports match events into structured story packs. Its primary functions include:

- **Event Conversion**: Facilitates the transformation of sports match events into a narrative form, utilizing a dedicated Python script, `storyteller.py`.
- **Scoring Heuristic System**: Implements the `core.py`, which features a scoring heuristic to rank events based on their significance, considering the type of event and the context of the game.
- **Player Data Resolution**: Loads player squad data to ensure accurate identification of player names associated with the match events.
- **Asset Image Selection**: Selects relevant visual assets for each event based on predefined criteria.
- **JSON Story Pack Generation**: Produces JSON formatted story packs that include:
  - Cover page
  - Top N highlight pages (default is set to 7)
  - Closing page
- **Debugging and Testing**: Comes with auxiliary scripts that assist in testing the accuracy of asset selection and player squad data loading.
- **Modular Architecture**: The code is organized into separate modules for asset selection, squad management, and scoring logic facilitating easy maintenance and extension of functionalities.