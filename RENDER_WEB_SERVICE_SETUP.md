# NewAir - Render Web Service

Si `/api/discord/login` affiche `Not Found`, le site est encore déployé en **Static Site**.

Les fonctions Discord, le panel admin, les rôles acceptés/refusés et les comptes liés ont besoin de `server.py`. Donc il faut lancer le projet en **Web Service Python**.

## À faire sur Render

1. Crée un nouveau service Render.
2. Choisis **Web Service**, pas Static Site.
3. Connecte ce repo GitHub : `zakaribrouncha-cmyk/NewAir-SITE`.
4. Mets :

```txt
Runtime: Python
Build Command: laisser vide
Start Command: python server.py
```

5. Remets les variables ENV Discord dans ce Web Service :

```env
PUBLIC_BASE_URL=https://newair-site.onrender.com
DISCORD_CLIENT_ID=...
DISCORD_CLIENT_SECRET=...
DISCORD_BOT_TOKEN=...
DISCORD_GUILD_ID=...
DISCORD_ADMIN_ROLE_IDS=...
DISCORD_STAFF_ROLE_IDS=...
DISCORD_SUPERADMIN_ROLE_IDS=...
DISCORD_FONDATEUR_ROLE_IDS=...
DISCORD_HAUT_GRADE_PANEL_ROLE_IDS=...
DISCORD_ACCEPTED_ROLE_ID=1523767412103708762
DISCORD_REFUSED_ROLE_ID=1523768172291948674
```

6. Dans Discord Developer Portal, Redirect URI :

```txt
https://newair-site.onrender.com/api/discord/callback
```

## Test

Après déploiement, ces routes doivent répondre :

```txt
/api/discord/login?mode=user&next=/compte
/api/team
/api/user/me
/admin/joueurs/
```
