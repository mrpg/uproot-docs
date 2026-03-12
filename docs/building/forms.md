# Collecting data with forms

Forms are how you collect responses from participants. Define form fields on your page, and uproot handles rendering, validation, and storage automatically.

## The fields dictionary

Define fields as a dictionary on your page class:

```python
class Survey(Page):
    fields = dict(
        age=IntegerField(label="How old are you?", min=18, max=100),
        feedback=StringField(label="Any comments?", optional=True),
    )
```

Field names become attributes on the player object. After submission, access the data as `player.age` and `player.feedback`.

## Available field types

### Text fields

**StringField** — Single-line text input:

```python
name=StringField(label="Your name")
```

**TextAreaField** — Multi-line text input:

```python
comments=TextAreaField(label="Additional comments", optional=True)
```

**EmailField** — Email input with validation:

```python
email=EmailField(label="Email address")
```

### Numeric fields

**IntegerField** — Whole numbers:

```python
age=IntegerField(label="Age", min=0, max=120)
```

**DecimalField** — Decimal numbers:

```python
amount=DecimalField(label="Amount to contribute", min=0.0, max=100.0)
```

### Selection fields

**RadioField** — Choose one option with radio buttons:

```python
choice=RadioField(
    label="Do you agree?",
    choices=[(True, "Yes"), (False, "No")],
)
```

**SelectField** — Dropdown selection:

```python
country=SelectField(
    label="Country",
    choices=[
        ("us", "United States"),
        ("uk", "United Kingdom"),
        ("de", "Germany"),
    ],
)
```

**BooleanField** — Checkbox:

```python
consent=BooleanField(label="I agree to participate")
```

### Scales and sliders

**LikertField** — Rating scale with labeled endpoints:

```python
satisfaction=LikertField(
    label="How satisfied are you?",
    label_min="Very unsatisfied",
    label_max="Very satisfied",
    min=1,
    max=7,
)
```

**DecimalRangeField** — Slider input:

```python
confidence=DecimalRangeField(
    label="Confidence level",
    min=0,
    max=100,
    step=1,
)
```

### Other fields

**DateField** — Date picker:

```python
birthdate=DateField(label="Date of birth")
```

**FileField** — File upload (see [File uploads](../advanced/uploads.md)):

```python
document=FileField(label="Upload your document")
```

## Field options

All fields support these common options:

| Option | Description | Default |
|--------|-------------|---------|
| `label` | Question text shown to participant | `""` |
| `optional` | Allow empty responses | `False` |
| `description` | Help text below the field | `None` |
| `default` | Pre-filled value | `None` |

### Numeric constraints

`IntegerField` and `DecimalField` support `min` and `max`:

```python
donation=IntegerField(
    label="How much do you donate?",
    min=0,
    max=100,
    description="Enter a value between 0 and 100",
)
```

### Choice formats

For `RadioField` and `SelectField`, choices can be:

```python
# List of (value, label) tuples
choices=[(1, "Option A"), (2, "Option B")]

# Dictionary
choices={"a": "Option A", "b": "Option B"}

# Simple boolean (RadioField only)
choices=[(True, "Yes"), (False, "No")]
```

The value is what gets stored; the label is what participants see.

### Radio button layout

Control radio button arrangement with `layout`:

```python
# Vertical (default)
choice=RadioField(label="Pick one", choices=[...], layout="vertical")

# Horizontal
choice=RadioField(label="Pick one", choices=[...], layout="horizontal")
```

## Rendering fields in templates

Fields render automatically when you extend the base template:

```html+jinja
{% extends "_uproot/Page.html" %}

{% block content %}
<h1>Survey</h1>
{{ fields() }}
{% endblock %}
```

To render fields individually with custom layout:

```html+jinja
{% block content %}
<div class="row">
    <div class="col-6">{{ field(form.age) }}</div>
    <div class="col-6">{{ field(form.income) }}</div>
</div>

{{ field(form.comments) }}
{% endblock %}
```

## Form validation

### Built-in validation

Fields validate automatically based on their type and options:

- Required fields must have a value (unless `optional=True`)
- Numeric fields check `min` and `max` bounds
- Email fields check format

Invalid submissions show error messages and keep the participant on the page.

### Custom validation

Add a `validate` method for custom validation logic:

```python
class Allocation(Page):
    fields = dict(
        give_a=IntegerField(label="Give to A", min=0, max=100),
        give_b=IntegerField(label="Give to B", min=0, max=100),
    )

    @classmethod
    def validate(page, player, data):
        if data["give_a"] + data["give_b"] > 100:
            return "Total cannot exceed 100"
```

The `data` parameter contains submitted values as a dictionary. Return a string (or list of strings) if there's an error. Return nothing if validation passes.

### Async validation

The validate method can be async for database lookups or external checks:

```python
@classmethod
async def validate(page, player, data):
    if await username_taken(data["username"]):
        return "Username already exists"
```

## Dynamic fields

Generate fields based on player state using the `fields` method:

```python
class DynamicSurvey(Page):
    @classmethod
    def fields(page, player):
        choices = [
            (i, f"Option {i}")
            for i in range(1, player.num_options + 1)
        ]
        return dict(
            selection=SelectField(label="Choose:", choices=choices),
        )
```

This is useful for:

- Personalizing questions based on prior responses
- Showing different options per experimental condition
- Building adaptive surveys
- Setting field constraints based on other players' choices (in multiplayer games)

:material-github: [See dynamic fields in the trust_game example](https://github.com/mrpg/uproot-examples/tree/master/trust_game)

## Stealth fields

Stealth fields are processed separately instead of being saved automatically. Use them for file uploads or when you need custom handling logic.

### Defining stealth fields

Mark fields as stealth and provide a handler:

```python
class UploadPage(Page):
    fields = dict(
        name=StringField(label="Your name"),
        photo=FileField(label="Upload a photo"),
    )

    stealth_fields = ["photo"]

    @classmethod
    async def handle_stealth_fields(page, player, photo=None):
        if photo is not None:
            content = await photo.read()
            player.photo_size = len(content)
            player.photo_name = photo.filename
```

The `name` field saves automatically to `player.name`. The `photo` field is passed to `handle_stealth_fields` instead.

### Validation in stealth handlers

Return error messages to reject the submission:

```python
@classmethod
async def handle_stealth_fields(page, player, document=None):
    if document is None:
        return "Please upload a document"

    content = await document.read()
    if len(content) > 5_000_000:
        return "File too large (max 5MB)"

    # Process the file...
    player.doc_size = len(content)
```

### Dynamic stealth fields

Use a method instead of a list for dynamic stealth field names:

```python
@classmethod
def stealth_fields(page, player):
    return ["response"] if player.condition == "special" else []
```

Stealth fields are ideal for sensitive data like payment information that shouldn't be stored in the main database:

```python
class PaymentForm(Page):
    fields = dict(
        iban=IBANField(label="Your IBAN"),
        rating=DecimalRangeField(label="Rate this experiment", min=0, max=5),
    )

    stealth_fields = ["iban"]

    @classmethod
    async def handle_stealth_fields(page, player, iban: str):
        # Write to separate secure storage, send to payment processor, etc.
        print(f"Payment data for {player}: {iban}")
```

:material-github: [See the payment_data example](https://github.com/mrpg/uproot-examples/tree/master/payment_data)

## Accessing submitted data

After form submission, field values are automatically saved to the player:

```python
class Results(Page):
    @classmethod
    def templatevars(page, player):
        return dict(
            their_age=player.age,           # From IntegerField
            their_choice=player.choice,     # From RadioField
        )
```

Values are stored with their proper types—integers stay integers, booleans stay booleans.

## Complete example

Here's a complete page with multiple field types and validation:

```python
class Questionnaire(Page):
    fields = dict(
        age=IntegerField(
            label="What is your age?",
            min=18,
            max=100,
        ),
        gender=RadioField(
            label="What is your gender?",
            choices=[
                ("m", "Male"),
                ("f", "Female"),
                ("o", "Other"),
                ("na", "Prefer not to say"),
            ],
        ),
        risk=LikertField(
            label="How willing are you to take risks?",
            label_min="Not at all willing",
            label_max="Very willing",
            min=0,
            max=10,
        ),
        income=DecimalField(
            label="Annual income (in thousands)",
            min=0,
            max=10000,
            optional=True,
            description="This field is optional",
        ),
    )

    @classmethod
    def validate(page, player, data):
        if data["age"] < 18:
            return "You must be at least 18 to participate"
```

:material-github: [See forms in the quiz example](https://github.com/mrpg/uproot-examples/tree/master/quiz)
