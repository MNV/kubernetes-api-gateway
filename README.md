Архитектура решения

![image-20200512154011363](./README.assets/image-20200512154011363.png)

В начале убедиться, что nginx ingress запущен

```
➜  nginx-forward-auth git:(master) ✗ minikube addons  enable ingress
🌟  The 'ingress' addon is enabled
```

Собираем и запускаем с помощью skaffold сервис аутентификации

```bash
➜  nginx-forward-auth git:(master) ✗ cd auth
➜  auth git:(master) ✗ skaffold run
Generating tags...
 - auth -> auth:latest
Checking cache...
 - auth: Found Locally
Tags used in deployment:
 - auth -> auth:cde52ae856e0705fdcf80d8e5cf9254b8af5ec9b38eb61613010140d1e942f3a
   local images can't be referenced by digest. They are tagged and referenced by a unique ID instead
Starting deploy...
Helm release auth not installed. Installing...
```

И приложение, в котором мы будем проверять аутентификацию 
```bash
➜  nginx-forward-auth git:(master) ✗ cd app
➜  app git:(master) ✗ skaffold run
Generating tags...

 - app -> app:latest
Checking cache...
 - app: Found. Tagging
Tags used in deployment:
 - app -> app:1a4d7ceecee37bbce9f995c11dae74ec996c3c92bf7e673db03232eb32051427
   local images can't be referenced by digest. They are tagged and referenced by a unique ID instead
Starting deploy...
Helm release app not installed. Installing...
NAME: app
```

Применяем манифст для сервиса аутентификации
```bash
➜ nginx-forward-auth git:(master) ✗ kubectl apply -f auth-ingress.yaml

ingress.networking.k8s.io/auth-proxy created
```

В файле app-ingress.yaml выставлены настройки аутентификации через аннотации.

Auth-url - это урл, который осуществляет проверку на аутентификацию 
Стоит обратить внимание, что урл имеет полное доменное имя внутри кластера (вместе с указанием неймспейса - auth), потому что nginx запущен в другом неймспейсе. 

Также есть указание какие заголовки будут прокидываться в сервис app из сервиса auth.

```yaml
-- cat app-ingress.yaml
apiVersion: networking.k8s.io/v1beta1
kind: Ingress
metadata:
  name: app
  annotations:
    nginx.ingress.kubernetes.io/auth-url: "http://auth.auth.svc.cluster.local:9000/auth"
    nginx.ingress.kubernetes.io/auth-signin: "http://$host/signin"
    nginx.ingress.kubernetes.io/auth-response-headers: "X-User,X-Email,X-UserId,X-First-Name,X-Last-Name"
spec:
  rules:
  - host: arch.homework
    http:
      paths:
      - backend:
          serviceName: app
          servicePort: 9000
        path: /users/me
```

Применяем ингресс для приложения
```
➜  nginx-forward-auth git:(master) ✗ kubectl apply -f app-ingress.yaml
ingress.networking.k8s.io/app created
```

После настройки
Запускаем тесты с помощью newman и проверяем, что все корректно запустилось. 

```
→ регистрация пользователя 1
  POST http://arch.homework/register [200 OK, 147B, 58ms]
  ✓  [INFO] Request: {
	"login": "Helmer.Rodriguez", 
	"password": "tjY56BRfGTXxUq5",
	"email": "Aniya_Gibson@yahoo.com",
	"first_name": "Earnestine",
	"last_name": "Gislason"
}

  ✓  [INFO] Response: {
  "id": 37
}


→ проверка, что получение профиля пользователя недоступно без логина 
  GET http://arch.homework/users/me [401 UNAUTHORIZED, 207B, 15ms]
  ✓  [INFO] Request: [object Object]
  ✓  [INFO] Response: {
  "message": "Please go to login and provide Login/Password"
}


→ проверка, что изменение профиля пользователя недоступно без логина 
  PATCH http://arch.homework/profile [401 UNAUTHORIZED, 207B, 6ms]
  ✓  [INFO] Request: [object Object]
  ✓  [INFO] Response: {
  "message": "Please go to login and provide Login/Password"
}


→ вход пользователя 1
  POST http://arch.homework/login [200 OK, 236B, 9ms]
  ✓  [INFO] Request: {"login": "Helmer.Rodriguez", "password": "tjY56BRfGTXxUq5"}
  ✓  [INFO] Response: {
  "status": "ok"
}


→ изменение профиля пользователя 1
  PATCH http://arch.homework/profile [200 OK, 275B, 13ms]
  ✓  [INFO] Request: {
	"email": "Madyson_Zulauf@gmail.com",
	"first_name": "Chasity",
	"last_name": "Kessler"
}

  ✓  [INFO] Response: {
  "email": "Madyson_Zulauf@gmail.com", 
  "first_name": "Chasity", 
  "id": 37, 
  "last_name": "Kessler", 
  "login": "Helmer.Rodriguez"
}


→ проверка, что профиль поменялся 
  GET http://arch.homework/auth [200 OK, 395B, 6ms]
  ✓  [INFO] Request: [object Object]
  ✓  [INFO] Response: {
  "email": "Madyson_Zulauf@gmail.com", 
  "first_name": "Chasity", 
  "id": 37, 
  "last_name": "Kessler", 
  "login": "Helmer.Rodriguez"
}

  ✓  test token data

→ выход
  GET http://arch.homework/logout [200 OK, 225B, 6ms]
  ✓  [INFO] Request: [object Object]
  ✓  [INFO] Response: {
  "status": "ok"
}


→ получить данные после разлогина
  GET http://arch.homework/users/me [401 UNAUTHORIZED, 207B, 13ms]
  ✓  [INFO] Request: [object Object]
  ✓  [INFO] Response: {
  "message": "Please go to login and provide Login/Password"
}


→ регистрация пользователя 2
  POST http://arch.homework/register [200 OK, 147B, 17ms]
  ✓  [INFO] Request: {
	"login": "Isaiah.VonRueden46", 
	"password": "dnNbOetFTuz5Pey",
	"email": "Lysanne.Friesen@yahoo.com",
	"first_name": "Kyler",
	"last_name": "Wilderman"
}

  ✓  [INFO] Response: {
  "id": 38
}


→ вход пользователя 2
  POST http://arch.homework/login [200 OK, 236B, 8ms]
  ✓  [INFO] Request: {"login": "Isaiah.VonRueden46", "password": "dnNbOetFTuz5Pey"}
  ✓  [INFO] Response: {
  "status": "ok"
}


→ проверка, что пользователь 2 не имеет доступа на чтение и редактирование профиля пользователя 1 (auth)
  GET http://arch.homework/auth [200 OK, 401B, 6ms]
  ✓  [INFO] Request: [object Object]
  ✓  [INFO] Response: {
  "email": "Lysanne.Friesen@yahoo.com", 
  "first_name": "Kyler", 
  "id": 38, 
  "last_name": "Wilderman", 
  "login": "Isaiah.VonRueden46"
}

  ✓  test token data

→ проверка, что пользователь 2 не имеет доступа на чтение и редактирование профиля пользователя 1 (users/me)
  GET http://arch.homework/users/me [200 OK, 280B, 11ms]
  ✓  [INFO] Request: [object Object]
  ✓  [INFO] Response: {
  "email": "Lysanne.Friesen@yahoo.com", 
  "first_name": "Kyler", 
  "id": "38", 
  "last_name": "Wilderman", 
  "login": "Isaiah.VonRueden46"
}

  ✓  test token data

┌─────────────────────────┬──────────────────┬──────────────────┐
│                         │         executed │           failed │
├─────────────────────────┼──────────────────┼──────────────────┤
│              iterations │                1 │                0 │
├─────────────────────────┼──────────────────┼──────────────────┤
│                requests │               12 │                0 │
├─────────────────────────┼──────────────────┼──────────────────┤
│            test-scripts │               23 │                0 │
├─────────────────────────┼──────────────────┼──────────────────┤
│      prerequest-scripts │               15 │                0 │
├─────────────────────────┼──────────────────┼──────────────────┤
│              assertions │               27 │                0 │
├─────────────────────────┴──────────────────┴──────────────────┤
│ total run duration: 539ms                                     │
├───────────────────────────────────────────────────────────────┤
│ total data received: 864B (approx)                            │
├───────────────────────────────────────────────────────────────┤
│ average response time: 14ms [min: 6ms, max: 58ms, s.d.: 13ms] │
└───────────────────────────────────────────────────────────────┘
```
