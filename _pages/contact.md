---
layout: page
title: "Contact"
permalink: /contact/
---

The quickest way to reach me is [LinkedIn](https://www.linkedin.com/in/{{ site.author.linkedin }}/). I'm also on [GitHub](https://github.com/{{ site.author.github }}).

For email, write to <span id="contact-email" data-user="{{ site.author.contact_email_user }}" data-domain="{{ site.author.contact_email_domain }}"><noscript>{{ site.author.contact_email_user }} (at) {{ site.author.contact_email_domain }}</noscript></span>.

<script>
  (function () {
    var el = document.getElementById('contact-email');
    var address = el.dataset.user + '@' + el.dataset.domain;
    var link = document.createElement('a');
    link.href = 'mailto:' + address;
    link.textContent = address;
    el.appendChild(link);
  })();
</script>
