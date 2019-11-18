def stats(request):
    return {
        'times': request.session.get('page_times', {}),
        'visits': request.session.get('page_visits', {}),
        'times_total': request.session.get('times_total', 0),
        'visits_total': request.session.get('visits_total', 0)
    }
