
# Enhanced Input Integration for Home Assistant

This Home Assistant integration provides a service to create and manage long text input entities. These entities can store and display large amounts of text, making them useful for various purposes, such as storing notes, logs, or responses from AI LLMs for later use. This integration enhances the helpers available in Home Assistant.

## Features

* **Create and Manage Long Text Inputs:** Easily create, update, and delete long text input entities through Home Assistant services.
* **Persistent Storage:** The integration uses Home Assistant's storage mechanism to persist entity data across restarts.
* **User Interface Configuration:** The integration can be configured through the Home Assistant UI.
* **Entity Attributes:** Each entity displays its title as its state and provides the long text and its length as attributes.
* **Enhances Home Assistant Helpers:** Ideal for storing and managing data from AI LLM responses or other dynamic text sources.

## Installation

1.  **HACS (Home Assistant Community Store) (Recommended):**
    * Add this repository as a custom repository in HACS (type: Integration).
    * Search for "Enhanced Input" in HACS and install it.
    * Restart Home Assistant.

2.  **Manual Installation:**
    * Copy the `enhanced_input` folder into your Home Assistant's `custom_components` directory.
    * Restart Home Assistant.

## Configuration

1.  Go to "Settings" -> "Devices & Services" -> "Add Integration".
2.  Search for "Enhanced Input" and click on it.
3.  Follow the configuration flow (which typically involves just clicking "Submit").

## Services

### `enhanced_input.create_input_text`

Creates or updates a long text input entity.

**Service Data:**

* `name` (Required): The name of the entity.
* `text` (Optional): The long text to store. Defaults to an empty string.
* `title` (Optional): The title of the entity. Defaults to the entity's name.

**Example:**

```yaml
service: enhanced_input.create_input_text
data:
  name: AI Response
  text: This is a long text input.
  title: My Custom Title

```

### `enhanced_input.delete_input_text`

Deletes a long text input entity.

**Service Data:**

-   `name` (Required): The name of the entity to delete.

**Example:**



```yaml
service: enhanced_input.delete_input_text
data:
  name: AI Response

```

## Entity Attributes

Each long text input entity has the following attributes:

-   `long_text`: The stored long text.
-   `length`: The length of the stored text.

## Example Automation

This automation demonstrates how to generate content using an AI LLM (e.g., using the `conversation.agent` service) and store the response in a long text input entity.



```yaml
automation:
  - alias: Store AI Response
    trigger:
      - platform: event
        event_type: call_service
        event_data:
          domain: conversation
          service: agent
    action:
      - service: enhanced_input.create_input_text
        data:
          name: AI Response
          text: "{{ trigger.event.data.result.response.speech.plain.speech }}"
          title: "AI Response at {{ now().strftime('%Y-%m-%d %H:%M:%S') }}"

```

## TODO

-   Implement an enhanced input select entity.
-   Gather user suggestions for additional features and improvements.

## User Suggestions

We encourage users to suggest their ideas for enhancing this integration. Please open an issue on GitHub with your suggestions.

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request on GitHub.