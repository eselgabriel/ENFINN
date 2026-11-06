# Tarjeta digital FUE – Apple Wallet + Google Wallet

Tarjeta de presentación tipo ID para **Fundación UniEcuador** (Zulema Uribe):

- **Pase de Apple Wallet** (`.pkpass`) y **pase de Google Wallet**, con el mismo diseño: logo, nombre, teléfono, correo, web y código QR.
- **QR como pase físico**: el QR que aparece dentro del pase lleva a `…/w/`. Quien lo escanea con la cámara ve abrirse **"Agregar a Google Wallet"** en Android o **"Agregar a Apple Wallet"** en iPhone, y recibe una copia de la tarjeta. Así, la tarjeta se comparte de teléfono a teléfono sin límite.
- **QR de contacto (vCard)**: en la página web, la pestaña "Guardar contacto" muestra un segundo QR. Al escanearlo, el teléfono ofrece **"Agregar contacto"** al instante, sin internet. Si prefieres que sea este el QR del pase, cambia `"qr_del_pase"` a `"contacto"` en `config.json`.
- **Página web compartible** (`docs/index.html`): un solo enlace que se puede enviar a un número ilimitado de personas. Muestra la tarjeta, el QR (se agranda al tocarlo) y los botones *Agregar a Apple Wallet*, *Agregar a Google Wallet*, *Guardar contacto* y *Compartir*. En iPhone solo aparece el botón de Apple y en Android el de Google.

### Uso ilimitado

| Plataforma | Cómo se logra |
|---|---|
| Apple Wallet | Un mismo `.pkpass` público. Cualquiera lo descarga desde la página, y desde Wallet se puede reenviar (AirDrop, Mensajes, correo), porque `sharingProhibited` está en `false`. |
| Google Wallet | Un solo pase con `MULTIPLE_HOLDERS`. El mismo enlace sirve para todas las personas y todos sus teléfonos. |
| Cualquier teléfono | El QR y el archivo `contacto.vcf` funcionan sin Wallet. |


---

## Activación rápida (todo desde el teléfono, sin instalar nada)

El repositorio ya trae una automatización (`.github/workflows/tarjeta.yml`). Toma tus credenciales de los *secrets* de GitHub, genera los pases y publica la página en **https://eselgabriel.github.io/ENFINN/**. Tus llaves nunca quedan en el código.

**A. Publicar la página.** En GitHub, entra a tu repo → *Settings → Pages → Build and deployment → Source:* **GitHub Actions**.

**B. Google Wallet** (con tu cuenta de Google, gratis):
1. Entra a **pay.google.com/business/console**. Crea la cuenta de emisor (*Google Wallet API*) y copia el **Issuer ID**, que es un número largo.
2. En **console.cloud.google.com**: crea un proyecto y habilita **Google Wallet API** en *APIs y servicios → Biblioteca*. Luego, en *IAM → Cuentas de servicio*, crea una cuenta de servicio y, en *Claves → Agregar clave → JSON*, descarga el archivo.
3. Vuelve a la Wallet Console. En *Users → Invite a user*, pega el correo de la cuenta de servicio (termina en `iam.gserviceaccount.com`) con permiso **Developer**.
4. En GitHub, ve a *Settings → Secrets and variables → Actions*:
   - En la pestaña **Secrets** crea `GOOGLE_WALLET_SA_JSON` y pega **todo** el contenido del JSON.
   - En la pestaña **Variables** crea `GOOGLE_WALLET_ISSUER_ID` con tu Issuer ID.
5. En *Actions → Publicar tarjeta → Run workflow*, lanza la automatización. En unos 2 minutos el botón y el QR de Google Wallet quedan funcionando.

> Mientras la cuenta de emisor esté en **modo demo**, solo tu cuenta (y las que agregues como *test users*) puede guardar el pase. Para que funcione con cualquier persona, en la Wallet Console pide **Publishing access** (*Request publishing access*). Google suele revisarlo en pocos días.

**C. Apple Wallet** (opcional; necesita Apple Developer, USD 99 al año). Crea estos secrets:

- `APPLE_P12_BASE64`: el `.p12` en base64.
- `APPLE_P12_PASSWORD`: la contraseña del `.p12`.
- `APPLE_WWDR_BASE64`: el certificado WWDR G4 en base64.

Y estas variables: `APPLE_TEAM_ID` y `APPLE_PASS_TYPE_ID`. Más detalles abajo.

---

## 1. Editar los datos

Todos los datos están en **`config.json`**: nombre, cargo, teléfono, correos, web, colores e identificadores de Apple y Google. Cambia ahí y vuelve a generar.

> En el QR, los acentos se quitan (por ejemplo, "Fundacion") porque algunos lectores de Android los muestran mal. El archivo `.vcf` descargable sí conserva los acentos.

## 2. Generar

```bash
pip install -r requirements.txt
python3 scripts/build.py
```

Genera todo lo que se pueda con las credenciales que existan en `certs/`. Lo que falte se omite con un aviso.

## 3. Publicar la página (obligatorio para Google Wallet)

Google descarga el logo y el banner desde una URL pública, así que la carpeta `docs/` tiene que estar publicada en internet:

- **GitHub Pages**: *Settings → Pages → Branch: main, carpeta `/docs`*. (En repos privados, GitHub Pages requiere un plan de pago.)
- O súbela a `uniecuador.edu.ec/tarjeta` o a Netlify, Vercel, etc.

Pon esa dirección en `"sitio_publico"` dentro de `config.json` y vuelve a generar.

## 4. Apple Wallet

Requiere una cuenta de **Apple Developer** (USD 99 al año).

1. En developer.apple.com → *Certificates, IDs & Profiles → Identifiers*, crea un **Pass Type ID**, por ejemplo `pass.ec.edu.uniecuador.tarjeta`.
2. Crea su **certificado** (*Certificates → Pass Type ID Certificate*), ábrelo en Llavero en un Mac y expórtalo como **`certs/pass.p12`** con contraseña.
3. Descarga el certificado intermedio **Apple WWDR G4** (en apple.com/certificateauthority) y guárdalo como **`certs/AppleWWDRCAG4.cer`**.
4. En `config.json`, completa `pass_type_identifier` y `team_identifier` (es el Team ID de 10 caracteres de tu cuenta).
5. Genera el pase:
   ```bash
   export APPLE_P12_PASSWORD='tu-contraseña'
   python3 scripts/build.py
   ```
   El resultado queda en `docs/tarjeta-fue.pkpass`. El servidor debe entregarlo con el tipo `application/vnd.apple.pkpass`; GitHub Pages ya lo hace así.

Para probar el empaquetado sin certificados: `python3 scripts/build_apple_pass.py --prueba`. Ese archivo de prueba no abre en Wallet.

## 5. Google Wallet

Es gratis.

1. Entra a **pay.google.com/business/console**, activa la **Google Wallet API** y copia tu **Issuer ID** en `config.json`.
2. En **Google Cloud Console**: crea un proyecto, habilita la *Google Wallet API*, crea un **service account** y descarga su llave JSON como **`certs/google-service-account.json`**.
3. En la Wallet Console, ve a *Users* y agrega el correo del service account con permiso de *Developer*.
4. Publica `docs/` (paso 3) y genera:
   ```bash
   python3 scripts/build.py
   ```
   El pase se crea o se actualiza por la API, y el enlace "Agregar a Google Wallet" queda en `docs/google-wallet-link.txt` y dentro de la página.

Mientras la cuenta de emisor esté en *modo demo*, solo las cuentas de prueba pueden guardar el pase. Para el público general, en la Wallet Console pide *Publishing access*.

Si no quieres usar la API: `python3 scripts/build_google_pass.py --sin-api`. En ese caso el pase se crea con el primer guardado, pero los cambios posteriores necesitan la API.

## Estructura

```
config.json                 datos de la tarjeta (editar aquí)
assets/logo-fue.png         logo original
scripts/
  build.py                  genera todo
  build_assets.py           QR, .vcf e imágenes
  build_apple_pass.py       .pkpass firmado
  build_google_pass.py      pase de Google y enlace
  build_site.py             página web
  site_template.html        diseño de la página
docs/                       sitio público (se publica tal cual)
certs/                      credenciales (NUNCA se suben; están en .gitignore)
```

## Seguridad

- No subas nunca `certs/` (está en `.gitignore`).
- Los botones usan textos propios. Si se quiere, se pueden reemplazar por las insignias oficiales de "Add to Apple Wallet" y "Add to Google Wallet", que piden las guías de marca de Apple y Google.
