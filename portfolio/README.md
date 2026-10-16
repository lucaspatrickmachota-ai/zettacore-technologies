# Portfolio website

A responsive personal portfolio presenting junior-level software development and cybersecurity learning projects.

## Live site

https://lucas-tech-portfolio.onrender.com/

## Contents

- `index.html` — the portfolio page, styles, language selector, project descriptions, credential links, and visual effects.
- The page uses a Three.js module loaded from jsDelivr for its abstract 3D hero scene. A CSS-based visual fallback is included.
- Language options: English, Spanish, and Brazilian Portuguese.

## Preview locally

Because the page imports a JavaScript module, use a local static HTTP server rather than opening the file directly:

```bash
python3 -m http.server 8000
```

Then open http://localhost:8000/portfolio/ in your browser from the repository root.

## Deployment

The current Render static site publishes the `portfolio` directory from the `main` branch. Deploy settings may change; check the Render dashboard if the live site does not reflect the latest commit.

## Accessibility and limitations

- The page includes a reduced-motion preference for animation.
- The 3D visual is an abstract design concept, not live threat telemetry.
- Third-party Three.js delivery requires an internet connection.
- This page is a portfolio website, not a security product.

## Feedback

Please open a GitHub issue with a concise description, browser/device details, and reproducible steps where possible.
