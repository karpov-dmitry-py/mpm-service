def get_user_qs(model, user, limit=None):
    if limit is None:
        qs = model.objects.filter(user=user)
    else:
        qs = model.objects.filter(user=user)[:limit]
    return qs
