from AppFactory import AppFactory

if __name__ == '__main__':
    factory = AppFactory()
    app = factory.create_app()
    app.run(debug=False, host='0.0.0.0', port=5000)