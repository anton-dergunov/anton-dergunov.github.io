# Personal web site of Anton Dergunov

To run locally, `cd` to the directory and run:

```bash
bundle exec jekyll serve
```

Periodic refresh:

```bash
bundle update github-pages
bundle exec jekyll build   # sanity check it still builds
git add Gemfile.lock && git commit   # user commits manually
```
