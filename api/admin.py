from django.contrib import admin

from api.models import User, VerificationCode


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "public_id", "username", "telegram_id")
    search_fields = ("public_id", "username", "telegram_id")


@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "username", "telegram_id", "expires_at")
    search_fields = ("code", "username", "telegram_id")
    readonly_fields = ("code", "expires_at")
