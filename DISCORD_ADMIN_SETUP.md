# Lier le panel admin aux rôles Discord

Le panel `/admin/` est protégé par Discord OAuth. Seuls les comptes Discord qui possèdent un rôle autorisé sur ton serveur peuvent entrer.

## Variables à mettre sur Render

Dans Render > ton service > Environment, ajoute :

```env
PUBLIC_BASE_URL=https://newair-site.onrender.com
DISCORD_CLIENT_ID=ID_DE_TON_APPLICATION_DISCORD
DISCORD_CLIENT_SECRET=SECRET_DE_TON_APPLICATION_DISCORD
DISCORD_BOT_TOKEN=TOKEN_DU_BOT_DISCORD
DISCORD_GUILD_ID=ID_DE_TON_SERVEUR_DISCORD
DISCORD_ADMIN_ROLE_IDS=ID_ROLE_ADMIN,ID_ROLE_FONDATEUR
```

Tu peux mettre plusieurs rôles dans `DISCORD_ADMIN_ROLE_IDS`, séparés par des virgules.

## Dans le portail Discord Developer

1. Ouvre ton application Discord.
2. Va dans OAuth2.
3. Ajoute cette Redirect URI :

```txt
https://newair-site.onrender.com/api/discord/callback
```

4. Va dans Bot et copie le token pour `DISCORD_BOT_TOKEN`.
5. Invite le bot dans ton serveur Discord.

## Récupérer les IDs Discord

Dans Discord :

1. Active le mode développeur.
2. Clic droit sur ton serveur > Copier l’identifiant = `DISCORD_GUILD_ID`.
3. Clic droit sur le rôle admin > Copier l’identifiant = `DISCORD_ADMIN_ROLE_IDS`.

## Après modification

Sur Render, fais :

```txt
Manual Deploy > Deploy latest commit
```

Puis ouvre :

```txt
https://newair-site.onrender.com/admin/
```
