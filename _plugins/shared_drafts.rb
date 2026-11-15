# Publishes only the drafts marked `share: true` (listed on /drafts/, unindexed).
# The production build runs with --drafts --future, which would publish every draft and every
# future-dated post, so this hook removes the rest. Local `jekyll serve` is left alone.
Jekyll::Hooks.register :site, :post_read do |site|
  next unless Jekyll.env == "production"

  posts = site.posts.docs
  posts.reject! { |d| d.draft? ? !d.data["share"] : d.date > Time.now }
  posts.each do |d|
    next unless d.draft?
    d.data["shared_draft"] = true
    d.data["sitemap"] = false
  end
  site.config["show_drafts"] = false # jekyll-feed then skips the shared drafts
end
