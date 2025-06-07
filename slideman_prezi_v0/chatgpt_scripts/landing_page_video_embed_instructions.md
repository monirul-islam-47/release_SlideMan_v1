# How to Embed the Demo Video on the Landing Page

1. **Copy `video_player_snippet.html`** into your project’s `/partials` or directly into `index.html` just **below** the hero section.

```html
<!-- Hero Section -->
<section id="hero"> … </section>

<!-- Demo Video -->
{% include "video_player_snippet.html" %}
```

If you’re not using a templating engine, simply paste the snippet’s HTML & `<style>` block where desired.

2. **Place assets**

```
/assets/
  prezi_demo.mp4          ← final 90‑second video
  prezi_video_poster.jpg  ← 1280×720 still frame for poster
```

3. **Optimize**

- Compress the MP4 with `ffmpeg -crf 23 -preset veryslow`.
- Provide a WebM fallback for browsers that prefer it.

4. **Lazy‑load (optional)**

Add `loading="lazy"` inside the `<video>` tag to defer loading until in‑viewport:

```html
<video … loading="lazy">
```

5. **Analytics**

Attach a click listener to `#prezi-demo` to fire your preferred analytics event:

```js
document.getElementById('prezi-demo')
        .addEventListener('play', () =>
           gtag('event','video_play',{label:'prezi_demo'}));
```

That’s it—publish and the video will appear responsive, retina‑sharp, and fully compliant with the landing‑page styling.
