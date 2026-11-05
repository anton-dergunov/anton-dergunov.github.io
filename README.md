# Personal web site of Anton Dergunov

## Run it locally

The first time, and after the Gemfile changes:

```bash
bundle install
```

Then, from this directory:

```bash
bundle exec jekyll serve --drafts --future --livereload --disable-disk-cache --destination /tmp/blog-site
```

and open <http://localhost:4000>. The page reloads by itself when a file is saved. A draft is at its permalink, for example <http://localhost:4000/posts/2199/01/agent-memory-3-textual-memory/>.

- `--drafts` includes `_drafts/`, with its subfolders (`_drafts/agent-memory/`).
- `--future` includes posts dated in the future. Drafts are dated `2199-01-01`, so without it Jekyll skips them ("has a future date").
- `--disable-disk-cache` and `--destination /tmp/blog-site` keep Jekyll's working files out of Dropbox. This folder is synced by Dropbox, and reading a cache file while Dropbox is still syncing it can fail with `IO::TimeoutError` in `jekyll/cache.rb`. Building into `/tmp` also stops every rebuild from uploading the whole site.

To see the site as it will be published, leave out `--drafts --future`.

To read it on an iPad or a phone on the same Wi-Fi, add `--host 0.0.0.0`, which serves to the network rather than only to this Mac, and open `http://<this Mac's name>.local:4000` on the device (the name is in System Settings → General → Sharing → Local hostname; `scutil --get LocalHostName` prints it). If macOS asks whether `ruby` may accept incoming connections, allow it.

## Periodic refresh

```bash
bundle update
bundle exec jekyll build --disable-disk-cache --destination /tmp/blog-site   # sanity check it still builds
git add Gemfile.lock && git commit   # user commits manually
```
