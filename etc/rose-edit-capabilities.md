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

| Existing Feature                                        | Action Performed                                                                                                                                                | Questions/Comments                                                                                                                                                                                                                                                                     | Is It A Requirement For Rose II | Modifications Required For Rose II |
| ------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------- | ---------------------------------- |
|                                                         |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Menu options                                            |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| File >                                                  |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Open                                                    | Open configuration                                                                                                                                              |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Save                                                    | Save changes                                                                                                                                                    |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Check And Save                                          | Check and save changes                                                                                                                                          | Check all metadata incl. fail-if/warn-if and validator macros, then save. |                                 |                                    |
| Load All Apps                                           | Load All Apps                                                                                                                                                   | Option is enabled for rose-suite.conf but errors when selecting this option. Option is disabled for rose-app.conf                                                                                                                                                                      |                                 |                                    |
| Quit                                                    | Quits rose edit                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Edit >                                                  |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Undo                                                    | Undo changes across apps in sequence, one character at a time or one action at a time                                                                           |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Redo                                                    | Redo changes across apps in sequence, one character at a time or one action at a time                                                                           |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Undo/redo Viewer                                        | Pop up view of Undo/Redo stack as scrollable list of changes.                                                                                                   |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Find                                                    | Find search term in variable names and values within app. Found items are displayed in tabs by section.                                                         | If the user moves focus to a different cell and clicks the search icon again, it doesn't find the next instance of the search term, but instead continues to find the search term that was next in the original search.                                                                |                                 |                                    |
| Find Next                                               | Find next occurrence                                                                                                                                            | The menu option doesn't work. It does work with Ctrl+G but can jump erratically between tabs and as above does not find the next item if the user changes focus.                                                                                                                       |                                 |                                    |
| Preferences                                             | No functionality           |                                 |                                 |                                    |
| View (Checkboxes) >                                     |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| View Variables                                          |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| View Fixed Variables                                    | ?                                                                                                                                                               |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| View All Ignored Variables                              | View trigger ignored variables                                                                                                                                  | Ignored with !! (logically ignored) or ! (user ignored). Ignored variables are disabled. Ignored variables are ignored at runtime.                                                                                                                                                     |                                 |                                    |
| View User Ignored Variables                             | View user ignored variables                                                                                                                                     | Ignored with !  Ignored variables are disabled. Ignored variables are ignored at runtime. This menu option is disabled when 'View All Ignored Variables' is selected.                                                                                                                  |                                 |                                    |
| View Latent Variables                                   | Show variables defined in the metadata but not present in the configuration |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| View Pages                                              |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| View All Ignored Pages                                  | View trigger ignored pages/sections                                                                                                                             | Ignored with \[!!sectionname\] (logically ignored) or \[!sectionname\] (user ignored). Ignored sections are highlighted as being ignored at the top of the display page                                                                                                                |                                 |                                    |
| View User Ignored Pages                                 | View user ignored pages/sections                                                                                                                                | Ignored with \[!sectionname\] Ignored sections are highlighted as being ignored at the top of the display page. This menu option is disabled when 'View All Ignored Pages' is selected                                                                                                 |                                 |                                    |
| View Latent Pages                                       | Show pages (e.g. sections / namespaces) defined in the metadata but not present in the configuration |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Flag Variables                                          |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Flag No-metadata Variables                              | Flag all variables in all sections by adding a 'no metadata' flag. An icon is added to all variables in the display pane for all sections.                      | Unchecking this option does not remove the flag. Rechecking the option adds more flag icons in the display pane. Switching to another pane reduces the number of flags back to the correct number.                                                                                     |                                 |                                    |
| Flag Optional Variables                                 | Flag all variables in all sections by adding an 'optional' flag. An icon is added to all variables in the display pane for all sections.                        | Unchecking this option does not remove the flag. Rechecking the option adds more flag icons in the display pane. Switching to another pane reduces the number of flags back to the correct number.                                                                                     |                                 |                                    |
| Flag Opt Config Variables                               | Flag all optional config variables in all sections by adding an 'optional config' flag. An icon is added to all variables in the display pane for all sections. | Unchecking this option does not remove the flag. Rechecking the option adds more flag icons in the display pane. Switching to another pane reduces the number of flags back to the correct number. Hovering on the flag displays the effective option conf overrides and their values. |                                 |                                    |
| Other                                                   |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| View Status Bar                                         | Show/Hides the Status Bar                                                                                                                                       |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Metadata >                                              |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Refresh Metadata                                        | Reload the metadata from the filesystem | Used by metadata developers to test changes on the fly |                                 |                                    |
| Metadata Search Path                                    | Change the search path used to locate metadata | Used by metadata developers to point at their working copy rather than any site-deployed metadata |                                 |                                    |
| Switch off Metadata                                     | View the configuration with no metadata | The purpose of this is unclear |                                 |                                    |
| Layout Preferences (Checkboxes) >                       | To Do                                                                                                                                                           |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Hide Variable Descriptions                              | To Do                                                                                                                                                           |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Hide Variable Help                                      | To Do                                                                                                                                                           |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Hide Variable Titles                                    | To Do                                                                                                                                                           |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Upgrade                                                 | To Do                                                                                                                                                           |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Graph Metadata                                          | To Do                                                                                                                                                           |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Check fail-if, warn-if                                  | To Do                                                                                                                                                           |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Check All Validator Macros                              | To Do                                                                                                                                                           |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Auto-fix all configurations                             | To Do                                                                                                                                                           |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Tools >                                                 |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Run Suite                                               | Runs rose suite-run                                                                                                                                             |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Launch File Browser                                     | Opens a file browsing window                                                                                                                                    |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Launch Terminal                                         | Opens a terminal window                                                                                                                                         |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| View Output                                             | View output if available                                                                                                                                        |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Launch Suite Control GUI                                | Launch gcontrol if the suite is registered                                                                                                                      |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Page >                                                  |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Add >                                                   |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Add blank variable                                      | Adds a new variable to the pane                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Revert to Saved                                         | Reverts to saved configuration                                                                                                                                  |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Info                                                    | Displays section info                                                                                                                                           |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Help                                                    | ?                                                                                                                                                               | Help option is disabled                                                                                                                                                                                                                                                                |                                 |                                    |
| Web Help                                                | ?                                                                                                                                                               | Web Help option is disabled                                                                                                                                                                                                                                                            |                                 |                                    |
| Help >                                                  |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Documentation                                           | Link to Rose Documentation                                                                                                                                      |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| About                                                   | About text, Copyright, License and link to Rose in GitHub                                                                                                       |                                                                                                                                                                                                                                                                                        |                                 |                                    |
|                                                         |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
|                                                         |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Icon Menu options                                       |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Open                                                    | File > Open                                                                                                                                                     |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Save                                                    | File > Save                                                                                                                                                     |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Check and Save                                          | File > Check And Save                                                                                                                                           |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Load All Apps                                           | File > Load All Apps                                                                                                                                            |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Browse files                                            | Browse Files                                                                                                                                                    |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Undo                                                    | Edit > Undo                                                                                                                                                     |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Redo                                                    | Edit > Redo                                                                                                                                                     |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Add to page >                                           |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Add blank variable                                      | Page > Add > Add Blank Variable                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Revert page to saved                                    | Page > Revert to Saved                                                                                                                                          |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Search box - Find expression (Regex)                    | Edit > Find                                                                                                                                                     |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Find next                                               | Edit > Find Next                                                                                                                                                |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Check fail-if, warn-if and run all validator macros     | Metadata > Check fail-if, warn-if                                                                                                                               |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Auto-fix configurations (run built-in transform macros) | Metadata > Check All Validator Macros                                                                                                                           |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| View Output                                             | Tools > View Output                                                                                                                                             |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Launch Suite Control GUI                                | Toold > Launch Suite Control GUI                                                                                                                                |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Run suite                                               | Tools > Run Suite                                                                                                                                               |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Run suite pick list                                     | Rose suite-run popup                                                                                                                                            |                                                                                                                                                                                                                                                                                        |                                 |                                    |
|                                                         |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| On Page Functionality                                   |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Navigation (LHS)                                        |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Hover On Sections                                       | Display 'name: description'                                                                                                                                     |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Navigating Sections                                     |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Section Tree Drill Down                                 | Find and Select Section to display                                                                                                                              |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Right Click Section >                                   |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Add new section                                         | Add new section                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Rename a section                                        | Rename a section                                                                                                                                                |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Enable a section                                        | Enable a section                                                                                                                                                |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Ignore a section                                        | Ignore a section                                                                                                                                                |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Info                                                    | Display section info                                                                                                                                            |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Edit section comments…                                  | Add/Edit section comments                                                                                                                                       |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Graph Metadata                                          | Metadata > Graph Metadata                                                                                                                                       |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Remove a section…                                       | Remove a section                                                                                                                                                |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Panel width adjustment                                  | Resize panel                                                                                                                                                    |                                                                                                                                                                                                                                                                                        |                                 |                                    |
|                                                         |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Viewing/Editing Variables Options (RHS)                 |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Tabbed displays                                         | To display multiple configurations on the same page                                                                                                             | Some strange tab behaviour: The tabs seem to appear when applying the Undo/Redo functionality. Newly selected sections then show their content in the currently selected tab, unless a tab for that section is already open, in which case it switches to that tab.                    |                                 |                                    |
| Settings (icon)                                         |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Hover                                                   | Displays text: 'Variable options'                                                                                                                               |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Click >                                                 |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Info                                                    | Display info                                                                                                                                                    |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Help                                                    | ?                                                                                                                                                               | Help is disabled. Going to Layout preferences > Hide Variable Help (uncheck) -> This does not enable help or display it                                                                                                                                                                |                                 |                                    |
| Edit Comments                                           | Edit comments                                                                                                                                                   | Hover on '#' to see comments                                                                                                                                                                                                                                                           |                                 |                                    |
| User-Ignore                                             | User-Ignore/Enable variable                                                                                                                                     |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Remove                                                  | Removes tab                                                                                                                                                     |  This could be an x icon next to the field                                                                                                                                                                                                                                             |                                 |                                    |
| Input boxes                                             | Edit values                                                                                                                                                     |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Radio boxes                                             | Edit values                                                                                                                                                     |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Scrollable checkbox selector                            | Edit values                                                                                                                                                     |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Grids                                                   | Edit values                                                                                                                                                     |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| Pick-list                                               | Edit values                                                                                                                                                     |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| ….                                                      |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |
| ….                                                      |                                                                                                                                                                 |                                                                                                                                                                                                                                                                                        |                                 |                                    |

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
