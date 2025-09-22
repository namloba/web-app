# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import session, render_template, redirect, url_for, flash, request
from flask_login import (
    current_user,
    login_user,
    logout_user,
    login_required
)

from flask_dance.contrib.github import github
from flask_dance.contrib.google import google

from apps import db, login_manager
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm
from apps.authentication.models import Users, Farms
from apps.config import Config
from apps.authentication.util import verify_pass


@blueprint.route('/')
def route_default():
    return redirect(url_for('authentication_blueprint.login'))


# Login & Registration

@blueprint.route("/github")
def login_github():
    """ Github login """
    if not github.authorized:
        return redirect(url_for("github.login"))

    res = github.get("/user")
    return redirect(url_for('home_blueprint.index'))


@blueprint.route("/google")
def login_google():
    """ Google login """
    if not google.authorized:
        return redirect(url_for("google.login"))

    res = google.get("/oauth2/v1/userinfo")
    return redirect(url_for('home_blueprint.index'))

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    if 'login' in request.form:

        # read form data
        username = request.form['username']
        password = request.form['password']

        # Locate user
        user = Users.query.filter_by(username=username).first()

        # Check the password
        if user and verify_pass(password, user.password):

            login_user(user)
            return redirect(url_for('authentication_blueprint.farm_management'))

        # Something (user or pass) is not ok
        return render_template('accounts/login.html',
                               msg='Wrong user or password',
                               form=login_form)

    if not current_user.is_authenticated:
        return render_template('accounts/login.html',
                               form=login_form)
    return redirect(url_for('home_blueprint.index'))


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        username = request.form['username']
        email = request.form['email']

        # Check usename exists
        user = Users.query.filter_by(username=username).first()
        if user:
            return render_template('accounts/register.html',
                                   msg='Username already registered',
                                   success=False,
                                   form=create_account_form)

        # Check email exists
        user = Users.query.filter_by(email=email).first()
        if user:
            return render_template('accounts/register.html',
                                   msg='Email already registered',
                                   success=False,
                                   form=create_account_form)

        # else we can create the user
        user = Users(**request.form)
        db.session.add(user)
        db.session.commit()

        # Delete user from session
        logout_user()
        
        return render_template('accounts/register.html',
                               msg='User created successfully.',
                               success=True,
                               form=create_account_form)

    else:
        return render_template('accounts/register.html', form=create_account_form)


@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('authentication_blueprint.login'))


# Errors

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('home/page-404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('home/page-500.html'), 500


@blueprint.context_processor
def has_github():
    return {'has_github': bool(Config.GITHUB_ID) and bool(Config.GITHUB_SECRET)}

@blueprint.context_processor
def has_google():
    return {'has_google': bool(Config.GOOGLE_ID) and bool(Config.GOOGLE_SECRET)}

@blueprint.route('/farm-management', methods=['GET', 'POST'])
@login_required
def farm_management():
    if request.method == 'POST':
        # Thêm farm mới
        name = request.form.get('name')
        description = request.form.get('description')
        if name:
            try:
                current_user.add_farm(name, description)
                flash('Thêm farm thành công!', 'success')
            except Exception as e:
                flash(f'Lỗi: {str(e)}', 'danger')
        return redirect(url_for('authentication_blueprint.farm_management'))

    # Hiển thị danh sách farm
    farms = Farms.query.filter_by(user_id=current_user.id).all()
    return render_template('farm_management.html', farms=farms)

@blueprint.route('/farm-management/delete/<int:farm_id>', methods=['POST'])
@login_required
def delete_farm(farm_id):
    if current_user.delete_farm(farm_id):
        flash('Xóa farm thành công!', 'success')
    else:
        flash('Không tìm thấy farm hoặc không thể xóa!', 'danger')
    return redirect(url_for('authentication_blueprint.farm_management'))

@blueprint.route('/update_farm/<int:farm_id>', methods=['POST'])
@login_required
def update_farm(farm_id):
    name = request.form.get('name')
    description = request.form.get('description')
    farm = current_user.update_farm(farm_id, name, description)
    if farm:
        flash('Cập nhật farm thành công!', 'success')
    else:
        flash('Không tìm thấy farm hoặc không thể cập nhật!', 'danger')
    return redirect(url_for('authentication_blueprint.farm_management'))

@blueprint.route('/select-farm/<int:farm_id>', methods=['POST'])
@login_required
def select_farm(farm_id):
    farm = Farms.query.filter_by(id=farm_id, user_id=current_user.id).first()
    if farm:
        session['selected_farm_id'] = farm.id
        return redirect(url_for('authentication_blueprint.dashboard'))
    flash('Farm không tồn tại hoặc không thuộc về bạn!', 'danger')
    return redirect(url_for('authentication_blueprint.farm_management'))

@blueprint.route('/dashboard')
@login_required
def dashboard():
    farm_id = session.get('selected_farm_id')
    if not farm_id:
        return redirect(url_for('authentication_blueprint.farm_management'))
    farm = Farms.query.filter_by(id=farm_id).first()
    farm_name = farm.name if farm else "Chưa chọn farm"
    return render_template('home/index.html', farm_name=farm_name)