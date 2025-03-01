---
layout: archive
title: "CV"
permalink: /cv/
author_profile: true
redirect_from:
  - /resume
---

{% include base_path %}

Education
======
* Ph.D in Computer Science, University of Central Florida, 2029 (expected)
* CQF certification in Quantitative Finance, June 2023
* B.S. in Thermal Energy, Danang University of Science and Technology, 2013-2019

Work experience
======
* Quant Researcher
  * Riot Investment Group
  * Duties includes: Conduct quantitative finance researches

* QuantConnect Algorithmic Trading developer
  * Freelance
  * Duties included: Building trading algorithms

Publications
======
  <ul>{% for post in site.publications reversed %}
    {% include archive-single-cv.html %}
  {% endfor %}</ul>
  
Talks
======
  <ul>{% for post in site.talks reversed %}
    {% include archive-single-talk-cv.html  %}
  {% endfor %}</ul>
  
Teaching
======
  <ul>{% for post in site.teaching reversed %}
    {% include archive-single-cv.html %}
  {% endfor %}</ul>
