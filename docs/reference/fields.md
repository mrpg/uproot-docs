# Form fields

All fields accept keyword-only arguments. See [Collecting data with forms](../building/forms.md) for usage patterns.

## Common parameters

These parameters are available on most fields:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `label` | `str` | `""` | Question text shown to the participant |
| `optional` | `bool` | `False` | Allow empty responses |
| `description` | `str` | `""` | Help text below the field |
| `default` | any | `None` | Pre-filled value |
| `render_kw` | `dict` | `None` | HTML attributes for the input element |
| `widget` | any | `None` | Custom WTForms widget |
| `class_wrapper` | `str` | `None` | CSS class for the wrapper div |

## BooleanField

A single checkbox.

```python
consent=BooleanField(label="I agree to participate")
```

| Parameter | Type | Default |
|-----------|------|---------|
| `label` | `str` | `""` |
| `render_kw` | `dict` | `None` |
| `description` | `str` | `""` |
| `widget` | any | `None` |
| `default` | any | `None` |
| `class_wrapper` | `str` | `None` |
| `validators` | list | — |

## BoundedChoiceField

Multi-select checkboxes with min/max selection limits.

```python
topics=BoundedChoiceField(
    label="Select your preferred topics",
    choices=["Economics", "Psychology", "Sociology"],
    min=1,
    max=3,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `choices` | list or dict | — | Available options |
| `min` | `int` | `0` | Minimum number of selections |
| `max` | `int` | `None` | Maximum selections (`None` = unlimited) |
| `layout` | `str` | `"vertical"` | `"vertical"` or `"horizontal"` |
| `label` | `str` | `""` | |
| `description` | `str` | `""` | |
| `render_kw` | `dict` | `None` | |
| `widget` | any | `None` | |
| `default` | any | `None` | |
| `class_wrapper` | `str` | `None` | |

Returns a list of selected values.

:material-github: [See the bounded_choice example](https://github.com/mrpg/uproot-examples/tree/master/bounded_choice)

## DateField

A date picker.

```python
birthdate=DateField(label="Date of birth")
```

| Parameter | Type | Default |
|-----------|------|---------|
| `label` | `str` | `""` |
| `optional` | `bool` | `False` |
| `render_kw` | `dict` | `None` |
| `description` | `str` | `""` |
| `widget` | any | `None` |
| `default` | any | `None` |
| `class_wrapper` | `str` | `None` |

## DecimalField

Decimal number input with optional addons and min/max bounds.

```python
amount=DecimalField(
    label="Amount to contribute",
    min=0.0,
    max=100.0,
    step=0.01,
    addon_start="$",
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min` | number | — | Minimum value |
| `max` | number | — | Maximum value |
| `step` | number | — | Step increment |
| `addon_start` | `str` | — | Text before the input (e.g., `"$"`) |
| `addon_end` | `str` | — | Text after the input (e.g., `"EUR"`) |
| `class_addon_start` | `str` | `""` | CSS class for start addon |
| `class_addon_end` | `str` | `""` | CSS class for end addon |
| `label` | `str` | `""` | |
| `optional` | `bool` | `False` | |
| `render_kw` | `dict` | `None` | |
| `description` | `str` | `""` | |
| `widget` | any | `None` | |
| `default` | any | `None` | |
| `class_wrapper` | `str` | `None` | |

## DecimalRangeField

A slider input.

```python
confidence=DecimalRangeField(
    label="How confident are you?",
    min=0,
    max=100,
    step=1,
    label_min="Not at all",
    label_max="Completely",
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min` | number | — | Minimum value |
| `max` | number | — | Maximum value |
| `step` | number | `1.0` | Step increment |
| `label_min` | `str` | `None` | Label below left end (defaults to `str(min)`) |
| `label_max` | `str` | `None` | Label below right end (defaults to `str(max)`) |
| `label_max_min_class_suffix` | `str` | `"-custom"` | CSS class suffix for endpoint labels |
| `hide_popover` | `bool` | `False` | Hide the current value popover |
| `anchoring` | `bool` | `True` | Show initial slider position |
| `label` | `str` | `""` | |
| `optional` | `bool` | `False` | |
| `render_kw` | `dict` | `None` | |
| `description` | `str` | `""` | |
| `widget` | any | `None` | |
| `default` | any | `None` | |
| `class_wrapper` | `str` | `None` | |

:material-github: [See the input_elements example](https://github.com/mrpg/uproot-examples/tree/master/input_elements)

## EmailField

Email input with format validation.

```python
email=EmailField(label="Your email address")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `label_floating` | `str` | `None` | Floating label inside the input |
| `label` | `str` | `""` | |
| `optional` | `bool` | `False` | |
| `render_kw` | `dict` | `None` | |
| `description` | `str` | `""` | |
| `widget` | any | `None` | |
| `default` | any | `None` | |
| `class_wrapper` | `str` | `None` | |

## FileField

File upload. Always treated as a stealth field—process in `handle_stealth_fields`.

```python
document=FileField(label="Upload your document")
```

See [File uploads](../advanced/uploads.md) for details.

| Parameter | Type | Default |
|-----------|------|---------|
| `label` | `str` | `""` |
| `optional` | `bool` | `False` |
| `render_kw` | `dict` | `None` |
| `description` | `str` | `""` |
| `widget` | any | `None` |
| `default` | any | `None` |
| `class_wrapper` | `str` | `None` |

## IBANField

IBAN input with format validation (requires the `schwifty` library).

```python
iban=IBANField(label="Your IBAN")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `addon_start` | `str` | — | Text before the input |
| `addon_end` | `str` | — | Text after the input |
| `class_addon_start` | `str` | `""` | CSS class for start addon |
| `class_addon_end` | `str` | `""` | CSS class for end addon |
| `label_floating` | `str` | `None` | Floating label inside the input |
| `label` | `str` | `""` | |
| `optional` | `bool` | `False` | |
| `render_kw` | `dict` | `None` | |
| `description` | `str` | `""` | |
| `widget` | any | `None` | |
| `default` | any | `None` | |
| `class_wrapper` | `str` | `None` | |

:material-github: [See the payment_data example](https://github.com/mrpg/uproot-examples/tree/master/payment_data)

## IntegerField

Whole number input with optional addons and min/max bounds.

```python
age=IntegerField(label="How old are you?", min=18, max=100)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min` | `int` | — | Minimum value |
| `max` | `int` | — | Maximum value |
| `addon_start` | `str` | — | Text before the input |
| `addon_end` | `str` | — | Text after the input |
| `class_addon_start` | `str` | `""` | CSS class for start addon |
| `class_addon_end` | `str` | `""` | CSS class for end addon |
| `label` | `str` | `""` | |
| `optional` | `bool` | `False` | |
| `render_kw` | `dict` | `None` | |
| `description` | `str` | `""` | |
| `widget` | any | `None` | |
| `default` | any | `None` | |
| `class_wrapper` | `str` | `None` | |

## LikertField

Rating scale rendered as radio buttons with labeled endpoints.

```python
satisfaction=LikertField(
    label="How satisfied are you?",
    label_min="Very unsatisfied",
    label_max="Very satisfied",
    min=1,
    max=7,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min` | `int` | `1` | Lowest value |
| `max` | `int` | `7` | Highest value |
| `label_min` | `str` | `""` | Label below the lowest value |
| `label_max` | `str` | `""` | Label below the highest value |
| `label` | `str` | `""` | |
| `optional` | `bool` | `False` | |
| `render_kw` | `dict` | `None` | |
| `description` | `str` | `""` | |
| `widget` | any | `None` | |
| `default` | any | `None` | |
| `class_wrapper` | `str` | `None` | |

Auto-generates integer choices from `min` to `max`.

## RadioField

Choose one option with radio buttons.

```python
choice=RadioField(
    label="Do you agree?",
    choices=[(True, "Yes"), (False, "No")],
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `choices` | list, dict, or `None` | `None` | Options (defaults to `[True, False]` if `None`) |
| `layout` | `str` | `"vertical"` | `"vertical"` or `"horizontal"` |
| `label` | `str` | `""` | |
| `optional` | `bool` | `False` | |
| `render_kw` | `dict` | `None` | |
| `description` | `str` | `""` | |
| `widget` | any | `None` | |
| `default` | any | `None` | |
| `class_wrapper` | `str` | `None` | |

Choices can be:

- `list[tuple[value, label]]` — e.g., `[(1, "Option A"), (2, "Option B")]`
- `dict[value, label]` — e.g., `{"a": "Option A", "b": "Option B"}`
- `list[value]` — e.g., `[1, 2, 3]` (value and label are the same)

## SelectField

Dropdown selection.

```python
country=SelectField(
    label="Country",
    choices=[("us", "United States"), ("de", "Germany")],
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `choices` | list or dict | — | Options (required) |
| `label` | `str` | `""` | |
| `optional` | `bool` | `False` | |
| `render_kw` | `dict` | `None` | |
| `description` | `str` | `""` | |
| `widget` | any | `None` | |
| `default` | any | `None` | |
| `class_wrapper` | `str` | `None` | |

Accepts the same choice formats as `RadioField`.

## StringField

Single-line text input.

```python
name=StringField(label="Your name")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `addon_start` | `str` | — | Text before the input |
| `addon_end` | `str` | — | Text after the input |
| `class_addon_start` | `str` | `""` | CSS class for start addon |
| `class_addon_end` | `str` | `""` | CSS class for end addon |
| `label_floating` | `str` | `None` | Floating label inside the input |
| `label` | `str` | `""` | |
| `optional` | `bool` | `False` | |
| `render_kw` | `dict` | `None` | |
| `description` | `str` | `""` | |
| `widget` | any | `None` | |
| `default` | any | `None` | |
| `class_wrapper` | `str` | `None` | |

## TextAreaField

Multi-line text input.

```python
comments=TextAreaField(label="Additional comments", optional=True)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `addon_start` | `str` | — | Text before the input |
| `addon_end` | `str` | — | Text after the input |
| `class_addon_start` | `str` | `""` | CSS class for start addon |
| `class_addon_end` | `str` | `""` | CSS class for end addon |
| `label_floating` | `str` | `None` | Floating label inside the input |
| `label` | `str` | `""` | |
| `optional` | `bool` | `False` | |
| `render_kw` | `dict` | `None` | |
| `description` | `str` | `""` | |
| `widget` | any | `None` | |
| `default` | any | `None` | |
| `class_wrapper` | `str` | `None` | |

:material-github: [See all field types in the input_elements example](https://github.com/mrpg/uproot-examples/tree/master/input_elements)
