from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from dal import autocomplete
import random
from .models import Recipe, Category
from .forms import RecipeForm, CommentForm, CategoryForm


def index(request):
    try:
        random_recipe = random.choice(Recipe.objects.all())
    except IndexError:
        random_recipe = Recipe.objects.none()
    context = {"random_recipe": random_recipe}
    return render(request, 'book/index.html', context)


def search_recipe(request):
    recipes = Recipe.objects.filter(
        published_date__lte=timezone.now()).order_by('published_date').reverse()
    count = recipes.count()
    if request.method == 'GET':
        search = request.GET.get('recipe_search')

        recipes = Recipe.objects.filter(
            Q(title__contains=search) | Q(categories__name__contains=search))

        if recipes.count() == 0:
            message = "Ingen resultater passet søket :("
        else:
            message = "Søket ga %s treff" % (recipes.count())
        return render(request, 'book/index.html', {'recipes': recipes,
                                                   'count': count,
                                                   'message': message})
    else:
        return render(request, 'book/index.html', {'recipes': recipes[:5],
                                                   'count': count})


def recipe_list(request, page=1):
    recipes_list = Recipe.objects.filter(published_date__lte=timezone.now()).order_by('title')
    paginator = Paginator(recipes_list, 6)

    try:
        recipes = paginator.page(page)
    except PageNotAnInteger:
        recipes = paginator.page(1)
    except EmptyPage:
        recipes = paginator.page(paginator.num_pages)

    context = {"recipes": recipes}
    return render(request, 'book/recipe_list.html', context)


def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    return render(request, 'book/recipe_detail.html', {'recipe': recipe})


@login_required
def recipe_new(request):
    if request.method == "POST":
        form = RecipeForm(request.POST)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.author = request.user
            recipe.published_date = timezone.now()
            recipe.save()
            form.save_m2m()
            return redirect('book:recipe_detail', pk=recipe.pk)
    else:
        form = RecipeForm()
    return render(request, 'book/recipe_edit.html', {'form': form})


@login_required
def recipe_edit(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == "POST":
        form = RecipeForm(request.POST, instance=recipe)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.author = request.user
            recipe.published_date = timezone.now()
            recipe.save()
            form.save_m2m()
            return redirect('book:recipe_detail', pk=recipe.pk)
    else:
        form = RecipeForm(instance=recipe)
    return render(request, 'book/recipe_edit.html', {'form': form,
                                                     'recipe': recipe})


@login_required
def recipe_remove(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    recipe.delete()
    return redirect('book:recipe_list')


def add_comment_to_recipe(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.recipe = recipe
            comment.save()
            return redirect('book:recipe_detail', pk=recipe.pk)
    else:
        form = CommentForm()
    return render(request, 'book/comment_to_recipe.html', {'form': form})


def category_list(request):
    categories = Category.objects.all().order_by("name")
    context = {"categories": categories}
    return render(request, "book/category_list.html", context)


def create_category(request):
    form = CategoryForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("book:category_list")

    context = {"form": form}
    return render(request, "book/category_new.html", context)


class CategoryAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated():
            return Category.objects.none()

        qs = Category.objects.all()
        if self.q:
            qs = qs.filter(name__istartswqith=self.q)

        return qs
