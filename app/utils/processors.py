# -*- coding: utf-8 -*-

import time
import random
import datetime

from flask import request, Markup, render_template_string
from flask.ext.restless.search import search as _search
from ..models import db, Article, Category, Tag, FriendLink, Link, Label, Topic
from helpers import get_category_ids


def utility_processor():
    """自定义模板处理器"""

    def archives():
        """
        返回从第一篇文章开始到现在所经历的月份列表
        """
        # archives = cache.get("archives")
        archives = None
        if archives is None:
            begin_post = Article.query.order_by('created').first()
            
            now = datetime.datetime.now()

            begin_s = begin_post.created if begin_post else now
            end_s = now

            begin = begin_s 
            end = end_s

            total = (end.year - begin.year) * 12 - begin.month + end.month
            archives = [begin]

            date = begin
            for i in range(total):
                if date.month < 12:
                    date = datetime.datetime(date.year, date.month + 1, 1)
                else:
                    date = datetime.datetime(date.year + 1, 1, 1)
                archives.append(date)
            archives.reverse()
            # cache.set("archives", archives)
        return archives

    def model_query(model, params):
        '''
        模型复杂查询

        :param model:
            实例模型，比如Article, Category, Tag, etc.
        :param params:
            参数字典，为dict类型，参照flask-restless文档

        特别注意：使用这个方法进行查询，模型`__mapper_args__`的
        `order_by`定义将会失效，在模板中使用时需要特别注意。

        详细内容请参照Flask-Restless的文档
        '''
        return _search(db.session, model, params)

    def category_tree():
        """
        返回栏目树形列表
        """
        return Category.tree()

    def get_related_articles(article_id, limit=10):
        """
        返回指定文章的相关文章列表
        
        根据Tag来筛选

        :param article_id:
            文章ID, 正整数
        :param limit:
            返回的个数, 正整数，默认为10
        """
        # 获取与本文章标签相同的所有文章ID
        article = Article.query.get(article_id)
        if article:
            ids = db.session.query('article_id') \
                            .from_statement( \
                                'SELECT article_id FROM ' \
                                'article_tags WHERE tag_id IN ' \
                                '(SELECT tag_id FROM article_tags ' \
                                'WHERE article_id=:article_id)') \
                            .params(article_id=article_id).all()

            article_ids = [_id[0] for _id in ids]
            article_ids = list(set(article_ids))

            if article_id in article_ids:
                article_ids.remove(article_id)

            random_ids = random.sample(article_ids, min(limit, len(article_ids)))

            if article_ids:
                return Article.query.public().filter(Article.id.in_(random_ids)).all()
        return None

    def get_top_articles(days=365, limit=10):
        """
        返回热门文章列表

        :param days:
            天数的范围，比如：一周7天，一个月30天。默认为一年
        :param limit:
            返回的个数，正整数，默认为10
        """
        criteria = []

        _start = datetime.date.today() - datetime.timedelta(days)
        criteria.append(Article.created >= _start)

        q = reduce(db.and_, criteria)
        return Article.query.public().filter(q) \
                                     .order_by(Article.hits.desc()) \
                                     .limit(int(limit)).all()

    def label(slug):
        """
        返回静态标签

        :param slug:
            英文标识符，unicode类型
        """
        s = Label.query.filter_by(slug=slug).first()
        return Markup(render_template_string(s.html)) if s is not None else ''

    return dict(
        Article=Article,
        Category=Category,
        Tag=Tag,
        Topic=Topic,
        FriendLink=FriendLink,
        model_query=model_query,
        get_category_ids=get_category_ids,
        archives=archives,
        get_top_articles=get_top_articles,
        category_tree=category_tree,
        get_related_articles=get_related_articles,
        label=label,
    )
