# Rôles Discord pour le panel admin NewAir

Le panel `/admin/` vérifie les rôles Discord avant de laisser entrer un membre.

## Staff, SuperAdmin, Fondateur

Le site utilise la variable Render `DISCORD_ADMIN_ROLE_IDS`. Mets dedans tous les rôles qui ont le droit d’ouvrir le panel :

```env
DISCORD_ADMIN_ROLE_IDS=ID_ROLE_STAFF,ID_ROLE_SUPERADMIN,ID_ROLE_FONDATEUR
```

Les IDs doivent être séparés par des virgules.

## Personne la plus haut gradée

Pour donner les mêmes permissions que Fondateur à une seule personne, crée un rôle Discord spécial, par exemple :

```txt
Haut Gradé Panel
```

Donne ce rôle uniquement à cette personne, puis ajoute l’ID du rôle dans `DISCORD_ADMIN_ROLE_IDS` :

```env
DISCORD_ADMIN_ROLE_IDS=ID_ROLE_STAFF,ID_ROLE_SUPERADMIN,ID_ROLE_FONDATEUR,ID_ROLE_HAUT_GRADE_PANEL
```

C’est plus propre et plus sûr que d’utiliser directement un ID utilisateur.

## Après changement

Sur Render, fais :

```txt
Manual Deploy > Deploy latest commit
```

Puis ouvre :

```txt
https://newair-site.onrender.com/admin/
```
