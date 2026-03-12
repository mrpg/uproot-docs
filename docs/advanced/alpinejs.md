# Using Alpine.js

uproot includes [Alpine.js](https://alpinejs.dev/start-here), a lightweight JavaScript framework for adding interactivity to templates. It's already loaded—no setup required.

## Essentials

```html+jinja
<!-- Reactive state + display -->
<div x-data="{ count: 0 }">
    <span x-text="count"></span>
    <button @click="count++">+1</button>
</div>

<!-- Show/hide -->
<div x-data="{ open: false }">
    <button @click="open = !open">Toggle</button>
    <p x-show="open">Now you see me</p>
</div>

<!-- Two-way input binding -->
<div x-data="{ name: '' }">
    <input x-model="name">
    <p>Hello, <span x-text="name"></span></p>
</div>

<!-- Loop -->
<ul x-data="{ items: ['A', 'B', 'C'] }">
    <template x-for="item in items">
        <li x-text="item"></li>
    </template>
</ul>

<!-- Conditional classes -->
<button x-data="{ on: false }" @click="on = !on" :class="{ 'active': on }">
    Toggle
</button>

<!-- Disabled state -->
<div x-data="{ val: '' }">
    <input x-model="val">
    <button :disabled="val.length < 3">Submit</button>
</div>
```

## Global stores

For state shared across the page, use `Alpine.store()`:

```html+jinja
<script>
document.addEventListener("alpine:init", () => {
    Alpine.store("game", { score: 0, level: 1 });
});
</script>

<div x-data>
    <p>Score: <span x-text="$store.game.score"></span></p>
    <button @click="$store.game.score++">+1</button>
</div>
```

## With live methods

Combine Alpine stores with `uproot.invoke()` for reactive server communication:

```html+jinja
<script>
document.addEventListener("alpine:init", () => {
    Alpine.store("task", { data: null, answer: "" });

    uproot.onReady(() => {
        uproot.invoke("get_puzzle").then(data => {
            Alpine.store("task").data = data;
        });
    });
});

function submit() {
    const store = Alpine.store("task");
    uproot.invoke("check", store.answer).then(ok => {
        if (ok) uproot.invoke("get_puzzle").then(d => store.data = d);
    });
}
</script>

<div x-data>
    <p x-text="$store.task.data?.question"></p>
    <input x-model="$store.task.answer" @keydown.enter="submit()">
    <button @click="submit()">Submit</button>
</div>
```

:material-github: [counter_alpine example](https://github.com/mrpg/uproot-examples/tree/master/counter_alpine) · [sumhunt example](https://github.com/mrpg/uproot-examples/tree/master/sumhunt) · [encryption_task example](https://github.com/mrpg/uproot-examples/tree/master/encryption_task)

## Quick reference

| Directive | Purpose | Example |
|-----------|---------|---------|
| `x-data` | Create reactive scope | `x-data="{ open: false }"` |
| `x-text` | Set text content | `x-text="message"` |
| `x-show` | Toggle visibility | `x-show="isVisible"` |
| `x-model` | Two-way bind input | `x-model="answer"` |
| `x-for` | Loop over array | `x-for="item in items"` |
| `@click` | Click handler | `@click="count++"` |
| `@keydown.enter` | Enter key handler | `@keydown.enter="submit()"` |
| `:class` | Conditional classes | `:class="{ 'active': on }"` |
| `:disabled` | Conditional disable | `:disabled="!ready"` |
| `$store` | Access global store | `$store.task.value` |

## Learn more

[Alpine.js documentation](https://alpinejs.dev/start-here)
