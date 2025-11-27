import web

urls = (
    "/", "Index",
    "/page_2", "Segundo",
    "/page_3", "Tercero",
    "/page_4", "Cuarto",
    "/page_5", "Quinto"
)

render = web.template.render("templates/")

app = web.application(urls, globals())

class Index:
    def GET(self):
        return render.index_html()


class Segundo:
    def GET(self):
        return render.page_2()


class Tercero:
    def GET(self):
        return render.page_3()


class Cuarto:
    def GET(self):
        return render.page_4()


class Quinto:
    def GET(self):
        return render.page_5()


if __name__ == "__main__":
    app.run()