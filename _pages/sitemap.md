---
layout: page
title: "Sitemap"
permalink: /sitemap/
---

Everything on this site. Robots may prefer the [XML version]({{ '/sitemap.xml' | relative_url }}).

## Pages

<ul>
{%- for p in site.pages -%}
  {%- if p.title and p.sitemap != false %}
  <li><a href="{{ p.url | relative_url }}">{{ p.title }}</a></li>
  {%- endif -%}
{%- endfor %}
</ul>

## Posts

<ul>
{%- for post in site.posts %}
  <li><a href="{{ post.url | relative_url }}">{{ post.title }}</a> <span class="date">{{ post.date | date: "%b %Y" }}</span></li>
{%- endfor %}
</ul>
