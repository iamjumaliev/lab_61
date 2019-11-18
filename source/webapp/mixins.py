from datetime import datetime

from django.views.generic import View

# Пример:
# 'page_visits': {
#     'page1': 5,
#     'page2': 6,
#     'page3': 4
# },
# 'page_times': {
#     'page1': 100,
#     'page2': 200,
#     'page3': 300
# },
# 'visits_total': 15,
# 'times_total': 600,
# last_page - хранит url предыдущей страницы.
# last_time - хранит время посещения предыдущей страницы, чтобы считать разницу от текущего.
#
#
class StatsMixin():
    def get(self, request, *args, **kwargs):
        self.update_page_visits()
        self.update_visits_total()
        last_page = request.session.get('last_page')
        now = datetime.now()
        if last_page:
            diff = self.get_time_spent(now)
            self.update_page_times(diff, last_page)
            self.update_times_total(diff)
        self.update_last_page_info(now)
        return super().get(request, *args, **kwargs)

    def update_page_visits(self):
        visits = self.request.session.get('page_visits', {})
        current_page_visits = visits.get(self.request.path, 0)
        current_page_visits += 1
        visits[self.request.path] = current_page_visits
        self.request.session['page_visits'] = visits

    def update_visits_total(self):
        total_visits = self.request.session.get('visits_total', 0)
        total_visits += 1
        self.request.session['visits_total'] = total_visits

    def get_time_spent(self, now):
        last_time = self.request.session.get('last_time')
        last_time = datetime.strptime(last_time, '%Y-%m-%d %H:%M:%S')
        return (now - last_time).total_seconds()

    def update_page_times(self, diff, last_page):
        times = self.request.session.get('page_times', {})
        last_page_time = times.get(last_page, 0)
        last_page_time += diff
        times[last_page] = last_page_time
        self.request.session['page_times'] = times

    def update_times_total(self, diff):
        total_time = self.request.session.get('times_total', 0)
        total_time += diff
        self.request.session['times_total'] = total_time

    def update_last_page_info(self, now):
        self.request.session['last_time'] = now.strftime('%Y-%m-%d %H:%M:%S')
        self.request.session['last_page'] = self.request.path
