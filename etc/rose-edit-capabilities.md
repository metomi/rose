# Rose Edit Capabilities

This document outlines the capabilities of `rose edit` in Rose 2019 and contains
proposals on how these capabilities will be mapped onto the proposed architecture
for the [new implementation](https://github.com/metomi/rose/issues/2615).

> **Definitions:**
>
> * json-Schema:
>   A JSON schema file (defines types, validation, etc).
> * form-schema:
>   A Json Form schema file (defines form inputs, structure, etc).
>   This is sometimes referred to as ui-schema
>   (as it is used to generate the UI).
> * converter:
>   The tool which will convert between Rose and JSON formats.
>
> * Inputs
>   Individual settings within a Rose configuration.
> * Configurations
>   Rose configurations. Each is associated with a file.


## Configuration

Rose Edit is a tool view viewing and editing Rose configurations, it provides no
support for other configuration / metadata formats.

> **Docs:**
> * [Application Configuration](http://metomi.github.io/rose/doc/html/api/configuration/application.html)
> * [Suite Configuration](http://metomi.github.io/rose/doc/html/api/configuration/suite.html)

### `key=value`

Rose Edit allows viewing/editing Rose configurations.

> **Proposal:**
> Convert Rose configurations into JSON (standardising types to
> match JSON schema) for use by the UI.

### `# comment`

Rose Edit supports viewing/editing comments associated with Rose configurations.

This feature has no direct mapping onto JSON Schema / JSON Schema Form.

> **Proposal:**
> * Consider whether the ability to edit comments is a hard requirement
>   ([requirements capture (6)](https://github.com/metomi/rose/issues/2648)).
> * If it is consider implementing via a separate interface.

####

## Metadata

Rose Edit uses metadata to:

* Choose an appropriate widget for each input.
* Layout the form in a logical way.
* Annotate configurations and provide contextual help.
* Performs on the fly-validation for quick checks.
* Performs on-demand validation for complex checks.
* Runs user-defined transformer macros on-demand.

> **Docs:**
> * [Metadata](http://metomi.github.io/rose/doc/html/api/configuration/metadata.html)

### Rose Metadata Items

#### ``ns``

* Defines form structure by allowing users to define a hierarchy.
* form-schema: `type: "Category"`

#### `sort-key`

* Defines the order of elements in any view of the form.
* form-schema: The order elements appear in the schema is the order they are
  displayed in.

#### `type`

* Defines the type of an input (see "Rose Types" below).
* json-schema: `type`

#### `length`

* Defines permitted length for arrays.
* json-schema: `type = "array"; maxlength; minlength`

#### `element titles`

* Defines column headings for gridded array inputs.
* form-schema: ``elementLabelProp`` (TODO: confirm)

#### `values`

* Defines an enum.
* json-schema: `type = "enum"`
* form-schema: `options: format: 'radio'`
* converter: convert into enum

#### `value-titles`

* Defines descriptions for enum values.
* Not presently supported in json-schema
  see: https://github.com/json-schema-org/json-schema-spec/issues/1062
* Would need to use anyOf rather than enum or template into the description.
* TODO

#### `value-hints`

* Hints (i.e. suggestions) for a variable.
* No obvious mapping onto JSON Schema.
* TODO.

#### `range`

* Defines numerical value ranges.
* json-schema: ``minimum; maximuml exclusiveMinimum; exclusiveMaximum``
* converter: convert from Rose range format into JSON fields.

#### `pattern`

* Defines a string pattern.
* json-schema: `regex`

#### `compulsory`

* Marks a field as required, note all fields are optional by default.
* json-schema: `required`

#### `duplicate`

* Permits duplicates (these are given a suffix).
* No obvious mapping onto json-schema.
* TODO

#### `title`

* Title for the input for display purposes.
* json-schema: `title`
* json-form: `label`

#### `description`

* Description for an input.
* json-schema: `description`

#### `help`

* Long description for an input.
* No analogue in json-schema, but can template into the description.
* json-schema: `description`

#### `url`

* A URL to associate with the input.
* No analogue in json-schema, but can template into the description.
* json-schema: `description`


### Rose Types

> **Docs:**
> * [Rose types documentation](http://metomi.github.io/rose/doc/html/api/configuration/metadata.html#metadata)

#### `boolean`
* Lower case boolean (`true`/`false`).
* json-schema: `type = "boolean"`

#### `logical`
* Fortran boolean (`.true.`/`.false.`).
* json-schema: `type = "boolean"`
* converter: convert to regular `boolean`

#### `python_boolean`
* Capitalised boolean (`True`/`False`).
* json-schema: `type = "boolean"`
* converter: convert to regular `boolean`

#### `character`
* String with length of one.
* json-schema: `type = "string"; regex`

#### `integer`
* Regular old integer.
* json-schema: `type = "integer"`

#### `python_list`
* Comma separated list contained in square brackets.
* json-schema: `type = "array"`
* converter: Parse as list.

#### `quoted`
* String with its containing quotes included.
* json-schema: `type = "string"`

#### `real`
* Number in scientific notation (e.g. `1.23E45`).
* json-schema: `type = "string"; regex`
* converter: Convert to regular number

#### `raw`
* Plain string.
* json-schema: `type = "string"`

#### `str_multi`
* Multi-line string.
* json-schema: `type = "string"`
* form-schema: `options: multi: true`

#### `spaced_list`
* Space separated list.
* json-schema: `type = "array"`


## Search & Filter

Rose Edit has a global-search bar which uses input names and allows inputs to
be filtered via the view menu.

> **TODO:**
> Explore the view options and search features and record the key capabilities.


## Widgets

Rose Edit provides widgets for:

* Viewing / editing inputs.
* Altering layout.
* Providing summaries.

> **Code:**
> * [pagewidget](https://github.com/metomi/rose/tree/2019.01.x/lib/python/rose/config_editor/pagewidget)
> * [valuewidget](https://github.com/metomi/rose/tree/2019.01.x/lib/python/rose/config_editor/valuewidget)
> * [panelwidget](https://github.com/metomi/rose/tree/2019.01.x/lib/python/rose/config_editor/panelwidget)

> **TODO:**
> Explore the widgets and record the key capabilities.


## Misc

Anything which doesn't fit into the above!

> **TODO: this**
