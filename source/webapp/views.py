from django.http import HttpResponseRedirect
from django.shortcuts import reverse, redirect, get_object_or_404

from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from webapp.forms import BasketOrderCreateForm, ManualOrderForm, OrderProductForm
from webapp.models import Product, OrderProduct, Order
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.contrib import messages


class IndexView(ListView):
    model = Product
    template_name = 'index.html'
    context_object_name = 'product_list'

    def get_queryset(self):
        return Product.objects.filter(in_order=True)


class ProductView( DetailView):
    model = Product
    template_name = 'product/detail.html'


class ProductCreateView(PermissionRequiredMixin, CreateView):
    model = Product
    template_name = 'product/create.html'
    fields = ('name', 'category', 'price', 'photo', 'in_order')
    permission_required = 'webapp.add_product', 'webapp.can_have_piece_of_pizza'
    permission_denied_message = '403 Доступ запрещён!'

    def get_success_url(self):
        return reverse('webapp:product_detail', kwargs={'pk': self.object.pk})


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    template_name = 'product/update.html'
    fields = ('name', 'category', 'price', 'photo', 'in_order')
    context_object_name = 'product'

    def get_success_url(self):
        return reverse('webapp:product_detail', kwargs={'pk': self.object.pk})


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = 'product/delete.html'
    success_url = reverse_lazy('webapp:index')
    context_object_name = 'product'

    def delete(self, request, *args, **kwargs):
        product = self.object = self.get_object()
        product.in_order = False
        product.save()
        return HttpResponseRedirect(self.get_success_url())


class BasketChangeView(View):
    def get(self, request, *args, **kwargs):
        products = request.session.get('products', [])

        pk = request.GET.get('pk')
        action = request.GET.get('action')
        next_url = request.GET.get('next', reverse('webapp:index'))

        if action == 'add':
            product = get_object_or_404(Product, pk=pk)
            if product.in_order:
                products.append(pk)
        else:
            for product_pk in products:
                if product_pk == pk:
                    products.remove(product_pk)
                    break

        request.session['products'] = products
        request.session['products_count'] = len(products)

        return redirect(next_url)


class BasketView(CreateView):
    model = Order
    form_class = BasketOrderCreateForm
    template_name = 'product/basket.html'
    success_url = reverse_lazy('webapp:index')

    def get_context_data(self, **kwargs):
        basket, basket_total = self._prepare_basket()
        kwargs['basket'] = basket
        kwargs['basket_total'] = basket_total
        return super().get_context_data(**kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        if self._basket_empty():
            form.add_error(None, 'В корзине отсутствуют товары!')
            return self.form_invalid(form)
        response = super().form_valid(form)
        self._save_order_products()
        self._clean_basket()
        messages.success(self.request, 'Заказ оформлен!')
        return response

    def _prepare_basket(self):
        totals = self._get_totals()
        basket = []
        basket_total = 0
        for pk, qty in totals.items():
            product = Product.objects.get(pk=int(pk))
            total = product.price * qty
            basket_total += total
            basket.append({'product': product, 'qty': qty, 'total': total})
        return basket, basket_total

    def _get_totals(self):
        products = self.request.session.get('products', [])
        totals = {}
        for product_pk in products:
            if product_pk not in totals:
                totals[product_pk] = 0
            totals[product_pk] += 1
        return totals

    def _basket_empty(self):
        products = self.request.session.get('products', [])
        return len(products) == 0

    def _save_order_products(self):
        totals = self._get_totals()
        for pk, qty in totals.items():
            OrderProduct.objects.create(product_id=pk, order=self.object, amount=qty)

    def _clean_basket(self):
        if 'products' in self.request.session:
            self.request.session.pop('products')
        if 'products_count' in self.request.session:
            self.request.session.pop('products_count')


class OrderListView(ListView):
    template_name = 'order/list.html'

    def get_queryset(self):
        if self.request.user.has_perm('webapp.view_order'):
            return Order.objects.all().order_by('-created_at')
        return self.request.user.orders.all()


class OrderDetailView(DetailView):
    template_name = 'order/detail.html'

    def get_queryset(self):
        if self.request.user.has_perm('webapp.view_order'):
            return Order.objects.all()
        return self.request.user.orders.all()


class OrderCreateView(CreateView):
    model = Order
    template_name = 'order/create.html'
    form_class = ManualOrderForm
    fields = ('user', 'first_name', 'last_name', 'phone', 'email')
    success_url = reverse_lazy('webapp:index')


class OrderDeliverView(View):
    def get(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=self.kwargs['pk'])
        order.status = 'delivered'
        order.save()
        return reverse('webapp:order_detail', kwargs={'pk': order.pk})


class OrderCancelView(View):
    def get(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=self.kwargs['pk'])
        order.status = 'canceled'
        order.save()
        return reverse('webapp:order_detail', kwargs={'pk': order.pk})


class OrderProductCreateView(CreateView):
    model = OrderProduct
    form_class = OrderProductForm
    template_name = 'order/create.html'

    def form_valid(self, form):
        order = get_object_or_404(Order, pk=self.kwargs['pk'])
        name_of_product = form.cleaned_data.get('product')
        amount_of_product = form.cleaned_data.get('amount')
        self.object = form.save(commit=False)
        self.object.order = order
        self.object.product = name_of_product
        self.object.amount = amount_of_product
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('webapp:order_detail', kwargs={'pk': self.object.order.pk})


# class OrderProductUpdateView(UpdateView):
#     model = OrderProduct
#     form_class = OrderProductForm
#     template_name = 'order/update.html'
#
#     def get_initial(self):
#         initial = super().get_initial()
#         self.project = get_object_or_404(Order, pk=self.kwargs['pk'])
#         initial['product'] = self.project.orderproduct_set.filter(order__orderproduct__in=self.project)
#         initial['amount'] = self.project.orderproduct_set
#         return initial
#
#     def get_success_url(self):
#         return reverse('webapp:order_detail', kwargs={'pk': self.object.order.pk})


class OrderProductDeleteView(DeleteView):
    model = OrderProduct
    context_object_name = 'order_product'
    pk_kwargs_url = 'pk'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return redirect(reverse('webapp:order_detail', kwargs={'pk': self.object.order.pk}))
