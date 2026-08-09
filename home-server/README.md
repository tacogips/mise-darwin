# darwin-mac-home-server

This directory is converged by `mise-darwin`.

- Service root: `__SERVICE_ROOT__`
- Data root: `__DATA_ROOT__`
- Backup root: `__BACKUP_ROOT__`

Start PiGallery2 with:

```sh
cd __SERVICE_ROOT__
docker compose up -d
```

Configure Jellyfin to read `__DATA_ROOT__/Videos` and
`__DATA_ROOT__/Photos`. Remote access should remain Tailscale-first; only
publish Caddy after TLS, authentication, and allowed hostnames are configured.
