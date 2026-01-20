from app.models import Recommendation, PollenData, UserAllergy

LOW_RISK = 10
MEDIUM_RISK = 40


def get_user_recommendations(user_profile, date, city):
    recommendations = set()

    allergies = UserAllergy.objects.select_related('pollen_type').filter(
        user=user_profile
    )

    for allergy in allergies:
        pollen = allergy.pollen_type

        data = PollenData.objects.filter(
            pollen_type=pollen,
            date=date,
            city=city
        )

        if not data.exists():
            continue

        avg_concentration = sum(d.concentration for d in data) / data.count()

        risk = (
            avg_concentration
            * pollen.allergenicity
            * allergy.sensitivity
        )

        if risk >= MEDIUM_RISK:
            recs = Recommendation.objects.filter(
                pollen_type=pollen
            )
            recommendations.update(recs)

        elif risk >= LOW_RISK:
            recs = Recommendation.objects.filter(
                category__in=['prevention', 'home'],
                pollen_type=pollen
            )
            recommendations.update(recs)

    # общие рекомендации (без привязки к пыльце)
    general = Recommendation.objects.filter(pollen_type__isnull=True)
    recommendations.update(general)

    return list(recommendations)
