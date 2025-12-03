# Portfolio Overview

This document provides a high-level summary of the portfolio site for **Do Hoang Vu**, an AI Engineer.

**Live Website:** hoangvu.id.vn  
**Code Repository:** `VuxPortfolio` on GitHub

### Purpose & Features

-   A polished, animated portfolio showcasing AI projects, research, blog posts, and engineering craft.
-   Built with **Next.js (App Router)**, **TypeScript**, **Tailwind CSS**, **Framer Motion**, and **Giscus** for comments.
-   Data-driven content using `src/data/profile.ts` for profile/projects and Markdown for blog content.
-   SEO optimized with dynamic sitemap, robots.txt, and Google Search Console integration.
-   Supports LaTeX/KaTeX math rendering in blog posts and interactive GitHub Discussions via Giscus.
-   Deployed using Next.js standalone build with Cloudflare tunnel on your custom domain.

-   Pages use **App Router** framework:
-   `/` – Home (hero, quick facts, skills, featured projects)
-   `/about` – About (background, education, interests, tech stack)
-   `/projects` – Filterable gallery of projects
-   `/projects/detail?project=<title>` – Detailed project view (auto-generates feature/challenges/results)
-   `/blog` – Blog index
-   `/blog/[slug]` – Individual blog article
-   `/resume` – Embedded PDF resume
-   `/contact` – Contact links
