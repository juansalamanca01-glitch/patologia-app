"""
Management command to seed the database with sample pathologies and form templates.
Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from informes.models import Patologia, Plantilla

Usuario = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with sample pathologies, templates, and a superuser.'

    def handle(self, *args, **options):
        # ── Create superuser ────────────────────────────
        if not Usuario.objects.filter(username='admin').exists():
            Usuario.objects.create_superuser(
                username='admin',
                email='admin@patologia.local',
                password='admin1234',
                nombre_completo='Administrador del Sistema',
                rol='admin',
            )
            self.stdout.write(self.style.SUCCESS('[OK] Superusuario "admin" creado (pass: admin1234)'))

        # ── Create sample pathologist ────────────────────
        if not Usuario.objects.filter(username='patologo1').exists():
            Usuario.objects.create_user(
                username='patologo1',
                email='patologo@patologia.local',
                password='patologo1234',
                nombre_completo='Dr. Carlos Méndez',
                rol='patologo',
                especialidad='Patología Quirúrgica',
            )
            self.stdout.write(self.style.SUCCESS('[OK] Patologo "patologo1" creado (pass: patologo1234)'))

        # ── Create auditor ──────────────────────────────
        if not Usuario.objects.filter(username='auditor1').exists():
            Usuario.objects.create_user(
                username='auditor1',
                email='auditor@patologia.local',
                password='auditor1234',
                nombre_completo='Lic. María García',
                rol='auditor',
            )
            self.stdout.write(self.style.SUCCESS('[OK] Auditor "auditor1" creado (pass: auditor1234)'))

        # ── Pathologies and templates ────────────────────
        patologias_data = [
            # ─── 1. BIOPSIA DE PIEL ──────────────────────
            {
                'nombre': 'Biopsia de Piel',
                'descripcion': 'Estudio histopatológico de tejido cutáneo.',
                'protocolo_medico': 'Fijar en formol al 10%. Incluir en su totalidad si mide menos de 2 cm.',
                'campos': [
                    {'campo_nombre': 'localizacion', 'campo_label': 'Localización anatómica', 'tipo_campo': 'texto', 'obligatorio': True, 'orden': 1},
                    {'campo_nombre': 'tipo_muestra', 'campo_label': 'Tipo de muestra', 'tipo_campo': 'lista', 'obligatorio': True, 'orden': 2, 'opciones': ['Punch', 'Escisional', 'Incisional', 'Shave']},
                    {'campo_nombre': 'dimensiones', 'campo_label': 'Dimensiones (cm)', 'tipo_campo': 'texto', 'obligatorio': True, 'orden': 3},
                    {'campo_nombre': 'color', 'campo_label': 'Color', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 4, 'opciones': ['Pardo', 'Blanquecino', 'Eritematoso', 'Pigmentado', 'Otro']},
                    {'campo_nombre': 'bordes', 'campo_label': 'Bordes', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 5, 'opciones': ['Regulares', 'Irregulares', 'Bien definidos', 'Mal definidos']},
                    {'campo_nombre': 'superficie', 'campo_label': 'Superficie', 'tipo_campo': 'texto', 'obligatorio': False, 'orden': 6},
                    {'campo_nombre': 'hallazgos_adicionales', 'campo_label': 'Hallazgos adicionales', 'tipo_campo': 'textarea', 'obligatorio': False, 'orden': 7},
                ],
            },
            # ─── 2. BIOPSIA DE MAMA ──────────────────────
            {
                'nombre': 'Biopsia de Mama',
                'descripcion': 'Estudio de tejido mamario para diagnóstico de lesiones benignas y malignas.',
                'protocolo_medico': 'Orientar la pieza. Medir en tres dimensiones. Cortes seriados cada 5 mm.',
                'campos': [
                    {'campo_nombre': 'lateralidad', 'campo_label': 'Lateralidad', 'tipo_campo': 'lista', 'obligatorio': True, 'orden': 1, 'opciones': ['Derecha', 'Izquierda']},
                    {'campo_nombre': 'tipo_muestra', 'campo_label': 'Tipo de muestra', 'tipo_campo': 'lista', 'obligatorio': True, 'orden': 2, 'opciones': ['Biopsia por aguja gruesa', 'Tumorectomía', 'Mastectomía', 'Biopsia incisional', 'Cuadrantectomía']},
                    {'campo_nombre': 'dimensiones', 'campo_label': 'Dimensiones (cm)', 'tipo_campo': 'texto', 'obligatorio': True, 'orden': 3},
                    {'campo_nombre': 'peso', 'campo_label': 'Peso (g)', 'tipo_campo': 'numero', 'obligatorio': False, 'orden': 4},
                    {'campo_nombre': 'tumor_tamanio', 'campo_label': 'Tamaño del tumor (cm)', 'tipo_campo': 'texto', 'obligatorio': False, 'orden': 5},
                    {'campo_nombre': 'margenes', 'campo_label': 'Márgenes quirúrgicos', 'tipo_campo': 'lista', 'obligatorio': True, 'orden': 6, 'opciones': ['Libres', 'Comprometidos', 'Cercanos (<2mm)', 'No valorables']},
                    {'campo_nombre': 'ganglios', 'campo_label': 'Ganglios linfáticos', 'tipo_campo': 'numero', 'obligatorio': False, 'orden': 7},
                    {'campo_nombre': 'necrosis', 'campo_label': 'Necrosis', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 8, 'opciones': ['Presente', 'Ausente']},
                    {'campo_nombre': 'observaciones', 'campo_label': 'Observaciones', 'tipo_campo': 'textarea', 'obligatorio': False, 'orden': 9},
                ],
            },
            # ─── 3. APÉNDICE CECAL ──────────────────────
            {
                'nombre': 'Apéndice Cecal',
                'descripcion': 'Estudio histopatológico de apéndice cecal post-apendicectomía.',
                'protocolo_medico': 'Medir longitud y diámetro. Seccionar longitudinalmente. Describir contenido luminal.',
                'campos': [
                    {'campo_nombre': 'tipo_muestra', 'campo_label': 'Tipo de muestra', 'tipo_campo': 'texto', 'obligatorio': True, 'orden': 1, 'valor_defecto': 'Apéndice cecal'},
                    {'campo_nombre': 'dimensiones', 'campo_label': 'Longitud x Diámetro (cm)', 'tipo_campo': 'texto', 'obligatorio': True, 'orden': 2},
                    {'campo_nombre': 'superficie', 'campo_label': 'Superficie serosa', 'tipo_campo': 'lista', 'obligatorio': True, 'orden': 3, 'opciones': ['Lisa y brillante', 'Opaca', 'Congestiva', 'Con exudado fibrinoso']},
                    {'campo_nombre': 'consistencia', 'campo_label': 'Consistencia', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 4, 'opciones': ['Blanda', 'Firme', 'Dura']},
                    {'campo_nombre': 'color', 'campo_label': 'Color', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 5, 'opciones': ['Pardo rosado', 'Congestivo', 'Verdoso', 'Negruzco']},
                    {'campo_nombre': 'hallazgos_adicionales', 'campo_label': 'Hallazgos adicionales', 'tipo_campo': 'textarea', 'obligatorio': False, 'orden': 6},
                ],
            },
            # ─── 4. VESÍCULA BILIAR ──────────────────────
            {
                'nombre': 'Vesícula Biliar',
                'descripcion': 'Estudio histopatológico de vesícula biliar post-colecistectomía.',
                'protocolo_medico': 'Medir en tres dimensiones. Abrir longitudinalmente. Describir mucosa y contenido.',
                'campos': [
                    {'campo_nombre': 'tipo_muestra', 'campo_label': 'Tipo de muestra', 'tipo_campo': 'texto', 'obligatorio': True, 'orden': 1, 'valor_defecto': 'Vesícula biliar'},
                    {'campo_nombre': 'dimensiones', 'campo_label': 'Dimensiones (cm)', 'tipo_campo': 'texto', 'obligatorio': True, 'orden': 2},
                    {'campo_nombre': 'superficie', 'campo_label': 'Superficie serosa', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 3, 'opciones': ['Lisa y brillante', 'Opaca', 'Adherencias']},
                    {'campo_nombre': 'consistencia', 'campo_label': 'Pared (espesor)', 'tipo_campo': 'texto', 'obligatorio': True, 'orden': 4},
                    {'campo_nombre': 'color', 'campo_label': 'Mucosa', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 5, 'opciones': ['Aterciopelada verde', 'Aterciopelada amarilla', 'Engrosada', 'Ulcerada']},
                    {'campo_nombre': 'calcificaciones', 'campo_label': 'Cálculos', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 6, 'opciones': ['Presente(s)', 'Ausente(s)']},
                    {'campo_nombre': 'numero_calculos', 'campo_label': 'Número de cálculos', 'tipo_campo': 'numero', 'obligatorio': False, 'orden': 7},
                    {'campo_nombre': 'observaciones', 'campo_label': 'Observaciones', 'tipo_campo': 'textarea', 'obligatorio': False, 'orden': 8},
                ],
            },
            # ─── 5. BIOPSIA DE PRÓSTATA ──────────────────
            {
                'nombre': 'Biopsia de Próstata',
                'descripcion': 'Biopsia por aguja de tejido prostático para estudio oncológico.',
                'protocolo_medico': 'Incluir cada cilindro por separado identificando la localización. Fijar en formol al 10%.',
                'campos': [
                    {'campo_nombre': 'tipo_muestra', 'campo_label': 'Tipo de procedimiento', 'tipo_campo': 'lista', 'obligatorio': True, 'orden': 1, 'opciones': ['Biopsia por aguja (TRUS)', 'Biopsia por fusión RM', 'Resección transuretral (RTU)', 'Prostatectomía radical']},
                    {'campo_nombre': 'num_cilindros', 'campo_label': 'Número de cilindros', 'tipo_campo': 'numero', 'obligatorio': True, 'orden': 2},
                    {'campo_nombre': 'localizacion', 'campo_label': 'Localización de los cilindros', 'tipo_campo': 'textarea', 'obligatorio': True, 'orden': 3},
                    {'campo_nombre': 'longitud_total', 'campo_label': 'Longitud total del tejido (cm)', 'tipo_campo': 'texto', 'obligatorio': True, 'orden': 4},
                    {'campo_nombre': 'color', 'campo_label': 'Color del tejido', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 5, 'opciones': ['Pardo blanquecino', 'Amarillento', 'Hemorrágico']},
                    {'campo_nombre': 'consistencia', 'campo_label': 'Consistencia', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 6, 'opciones': ['Blanda', 'Firme', 'Dura']},
                    {'campo_nombre': 'psa', 'campo_label': 'PSA sérico (ng/mL)', 'tipo_campo': 'numero', 'obligatorio': False, 'orden': 7},
                    {'campo_nombre': 'observaciones', 'campo_label': 'Observaciones', 'tipo_campo': 'textarea', 'obligatorio': False, 'orden': 8},
                ],
            },
            # ─── 6. TIROIDES ────────────────────────────
            {
                'nombre': 'Tiroides',
                'descripcion': 'Estudio histopatológico de glándula tiroides (nódulos, bocio, neoplasias).',
                'protocolo_medico': 'Pesar y medir. Seccionar en cortes seriados de 3 mm. Describir nódulos: tamaño, consistencia, aspecto.',
                'campos': [
                    {'campo_nombre': 'tipo_muestra', 'campo_label': 'Tipo de procedimiento', 'tipo_campo': 'lista', 'obligatorio': True, 'orden': 1, 'opciones': ['Lobectomía', 'Tiroidectomía total', 'Tiroidectomía subtotal', 'Biopsia por aguja fina (BAAF)', 'Istmectomía']},
                    {'campo_nombre': 'lateralidad', 'campo_label': 'Lateralidad', 'tipo_campo': 'lista', 'obligatorio': True, 'orden': 2, 'opciones': ['Lóbulo derecho', 'Lóbulo izquierdo', 'Bilateral', 'Istmo']},
                    {'campo_nombre': 'dimensiones', 'campo_label': 'Dimensiones del espécimen (cm)', 'tipo_campo': 'texto', 'obligatorio': True, 'orden': 3},
                    {'campo_nombre': 'peso', 'campo_label': 'Peso (g)', 'tipo_campo': 'numero', 'obligatorio': True, 'orden': 4},
                    {'campo_nombre': 'nodulo_presente', 'campo_label': '¿Nódulo identificado?', 'tipo_campo': 'lista', 'obligatorio': True, 'orden': 5, 'opciones': ['Sí, único', 'Sí, múltiples', 'No']},
                    {'campo_nombre': 'nodulo_tamanio', 'campo_label': 'Tamaño del nódulo (cm)', 'tipo_campo': 'texto', 'obligatorio': False, 'orden': 6},
                    {'campo_nombre': 'nodulo_aspecto', 'campo_label': 'Aspecto del nódulo', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 7, 'opciones': ['Sólido', 'Quístico', 'Mixto', 'Coloide', 'Calcificado']},
                    {'campo_nombre': 'capsula', 'campo_label': 'Estado de la cápsula', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 8, 'opciones': ['Intacta', 'Infiltrada', 'No valorable']},
                    {'campo_nombre': 'ganglios', 'campo_label': 'Ganglios linfáticos acompañantes', 'tipo_campo': 'numero', 'obligatorio': False, 'orden': 9},
                    {'campo_nombre': 'observaciones', 'campo_label': 'Observaciones', 'tipo_campo': 'textarea', 'obligatorio': False, 'orden': 10},
                ],
            },
            # ─── 7. COLON Y RECTO ────────────────────────
            {
                'nombre': 'Colon y Recto',
                'descripcion': 'Estudio de biopsias endoscópicas, polipectomías y resecciones colorrectales.',
                'protocolo_medico': 'En resecciones: medir longitud, identificar tumor, distancia a márgenes. En pólipos: medir e incluir completo.',
                'campos': [
                    {'campo_nombre': 'tipo_muestra', 'campo_label': 'Tipo de muestra', 'tipo_campo': 'lista', 'obligatorio': True, 'orden': 1, 'opciones': ['Biopsia endoscópica', 'Polipectomía', 'Colectomía parcial', 'Hemicolectomía derecha', 'Hemicolectomía izquierda', 'Sigmoidectomía', 'Resección anterior baja', 'Resección abdominoperineal', 'Colectomía total']},
                    {'campo_nombre': 'localizacion', 'campo_label': 'Localización', 'tipo_campo': 'lista', 'obligatorio': True, 'orden': 2, 'opciones': ['Ciego', 'Colon ascendente', 'Colon transverso', 'Colon descendente', 'Sigmoides', 'Recto', 'Unión rectosigmoidea']},
                    {'campo_nombre': 'dimensiones', 'campo_label': 'Dimensiones (cm)', 'tipo_campo': 'texto', 'obligatorio': True, 'orden': 3},
                    {'campo_nombre': 'tumor_tamanio', 'campo_label': 'Tamaño de la lesión/tumor (cm)', 'tipo_campo': 'texto', 'obligatorio': False, 'orden': 4},
                    {'campo_nombre': 'forma', 'campo_label': 'Morfología de la lesión', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 5, 'opciones': ['Polipoidea/exofítica', 'Ulcerada', 'Anular/estenosante', 'Plana', 'Sésil', 'Pediculada']},
                    {'campo_nombre': 'margenes', 'campo_label': 'Márgenes quirúrgicos', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 6, 'opciones': ['Libres', 'Comprometidos', 'No valorables']},
                    {'campo_nombre': 'ganglios', 'campo_label': 'Ganglios linfáticos identificados', 'tipo_campo': 'numero', 'obligatorio': False, 'orden': 7},
                    {'campo_nombre': 'perforacion', 'campo_label': 'Perforación', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 8, 'opciones': ['Presente', 'Ausente']},
                    {'campo_nombre': 'observaciones', 'campo_label': 'Observaciones', 'tipo_campo': 'textarea', 'obligatorio': False, 'orden': 9},
                ],
            },
            # ─── 8. ÚTERO Y CÉRVIX ──────────────────────
            {
                'nombre': 'Útero y Cérvix',
                'descripcion': 'Estudio de biopsias cervicales, legrados, LEEP/cono y piezas de histerectomía.',
                'protocolo_medico': 'En histerectomías: pesar, medir, abrir lateralmente. Describir endometrio, miometrio y cérvix.',
                'campos': [
                    {'campo_nombre': 'tipo_muestra', 'campo_label': 'Tipo de procedimiento', 'tipo_campo': 'lista', 'obligatorio': True, 'orden': 1, 'opciones': ['Biopsia cervical', 'Legrado endometrial', 'Legrado fraccionado', 'Cono/LEEP', 'Histerectomía total abdominal', 'Histerectomía vaginal', 'Histerectomía laparoscópica', 'Histerectomía con anexos']},
                    {'campo_nombre': 'dimensiones', 'campo_label': 'Dimensiones del útero (cm)', 'tipo_campo': 'texto', 'obligatorio': True, 'orden': 2},
                    {'campo_nombre': 'peso', 'campo_label': 'Peso (g)', 'tipo_campo': 'numero', 'obligatorio': False, 'orden': 3},
                    {'campo_nombre': 'endometrio', 'campo_label': 'Espesor endometrial (mm)', 'tipo_campo': 'texto', 'obligatorio': False, 'orden': 4},
                    {'campo_nombre': 'miometrio', 'campo_label': 'Miometrio', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 5, 'opciones': ['Homogéneo', 'Con nódulos (miomas)', 'Engrosado', 'Adelgazado']},
                    {'campo_nombre': 'num_miomas', 'campo_label': 'Número de miomas', 'tipo_campo': 'numero', 'obligatorio': False, 'orden': 6},
                    {'campo_nombre': 'mioma_mayor', 'campo_label': 'Tamaño del mioma mayor (cm)', 'tipo_campo': 'texto', 'obligatorio': False, 'orden': 7},
                    {'campo_nombre': 'cervix', 'campo_label': 'Aspecto del cérvix', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 8, 'opciones': ['Normal', 'Con lesión visible', 'Quistes de Naboth', 'Pólipo endocervical']},
                    {'campo_nombre': 'anexos', 'campo_label': 'Anexos incluidos', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 9, 'opciones': ['No incluidos', 'Ovarios y trompas bilaterales', 'Ovario y trompa derecha', 'Ovario y trompa izquierda']},
                    {'campo_nombre': 'observaciones', 'campo_label': 'Observaciones', 'tipo_campo': 'textarea', 'obligatorio': False, 'orden': 10},
                ],
            },
            # ─── 9. GANGLIO LINFÁTICO ────────────────────
            {
                'nombre': 'Ganglio Linfático',
                'descripcion': 'Estudio histopatológico de ganglio(s) linfático(s) para diagnóstico de linfomas, metástasis u otras patologías.',
                'protocolo_medico': 'Medir el ganglio. Seccionar en cortes de 2 mm. Fijar en formol. Reservar tejido en fresco si se sospecha linfoma.',
                'campos': [
                    {'campo_nombre': 'tipo_muestra', 'campo_label': 'Tipo de biopsia', 'tipo_campo': 'lista', 'obligatorio': True, 'orden': 1, 'opciones': ['Biopsia excisional', 'Biopsia incisional', 'Biopsia por aguja gruesa', 'Disección ganglionar']},
                    {'campo_nombre': 'localizacion', 'campo_label': 'Localización', 'tipo_campo': 'lista', 'obligatorio': True, 'orden': 2, 'opciones': ['Cervical', 'Axilar', 'Inguinal', 'Mediastinal', 'Retroperitoneal', 'Mesentérico', 'Supraclavicular', 'Otro']},
                    {'campo_nombre': 'num_ganglios', 'campo_label': 'Número de ganglios', 'tipo_campo': 'numero', 'obligatorio': True, 'orden': 3},
                    {'campo_nombre': 'dimensiones', 'campo_label': 'Dimensiones del mayor (cm)', 'tipo_campo': 'texto', 'obligatorio': True, 'orden': 4},
                    {'campo_nombre': 'color', 'campo_label': 'Color al corte', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 5, 'opciones': ['Pardo', 'Blanquecino', 'Amarillento', 'Hemorrágico', 'Negruzco']},
                    {'campo_nombre': 'consistencia', 'campo_label': 'Consistencia', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 6, 'opciones': ['Blanda', 'Firme', 'Dura', 'Elástica']},
                    {'campo_nombre': 'necrosis', 'campo_label': 'Necrosis', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 7, 'opciones': ['Presente', 'Ausente']},
                    {'campo_nombre': 'capsula', 'campo_label': 'Cápsula', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 8, 'opciones': ['Intacta', 'Infiltrada', 'Rota']},
                    {'campo_nombre': 'observaciones', 'campo_label': 'Observaciones', 'tipo_campo': 'textarea', 'obligatorio': False, 'orden': 9},
                ],
            },
            # ─── 10. BIOPSIA GÁSTRICA ────────────────────
            {
                'nombre': 'Biopsia Gástrica',
                'descripcion': 'Estudio histopatológico de biopsias gástricas obtenidas por endoscopia.',
                'protocolo_medico': 'Incluir todos los fragmentos. Identificar localización de cada toma. Fijar en formol al 10%.',
                'campos': [
                    {'campo_nombre': 'tipo_muestra', 'campo_label': 'Tipo de muestra', 'tipo_campo': 'lista', 'obligatorio': True, 'orden': 1, 'opciones': ['Biopsia endoscópica', 'Polipectomía gástrica', 'Mucosectomía', 'Gastrectomía parcial', 'Gastrectomía total']},
                    {'campo_nombre': 'localizacion', 'campo_label': 'Localización', 'tipo_campo': 'lista', 'obligatorio': True, 'orden': 2, 'opciones': ['Antro', 'Cuerpo', 'Fondo', 'Cardias', 'Píloro', 'Incisura', 'Curvatura mayor', 'Curvatura menor']},
                    {'campo_nombre': 'num_fragmentos', 'campo_label': 'Número de fragmentos', 'tipo_campo': 'numero', 'obligatorio': True, 'orden': 3},
                    {'campo_nombre': 'dimensiones', 'campo_label': 'Dimensiones agregadas (cm)', 'tipo_campo': 'texto', 'obligatorio': True, 'orden': 4},
                    {'campo_nombre': 'aspecto_endoscopico', 'campo_label': 'Hallazgo endoscópico', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 5, 'opciones': ['Mucosa normal', 'Gastritis eritematosa', 'Úlcera', 'Pólipo', 'Masa/tumor', 'Erosiones', 'Atrofia mucosa']},
                    {'campo_nombre': 'test_helicobacter', 'campo_label': 'Solicitan H. pylori', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 6, 'opciones': ['Sí', 'No']},
                    {'campo_nombre': 'observaciones', 'campo_label': 'Observaciones', 'tipo_campo': 'textarea', 'obligatorio': False, 'orden': 7},
                ],
            },
            # ─── 11. PULMÓN ─────────────────────────────
            {
                'nombre': 'Pulmón',
                'descripcion': 'Estudio histopatológico de biopsias bronquiales, transbronquiales y resecciones pulmonares.',
                'protocolo_medico': 'En resecciones: pesar, medir, insuflar con formol. Describir tumor y distancia a márgenes bronquial y vascular.',
                'campos': [
                    {'campo_nombre': 'tipo_muestra', 'campo_label': 'Tipo de procedimiento', 'tipo_campo': 'lista', 'obligatorio': True, 'orden': 1, 'opciones': ['Biopsia bronquial', 'Biopsia transbronquial', 'Biopsia por aguja percutánea', 'Segmentectomía', 'Lobectomía', 'Neumonectomía', 'Resección en cuña']},
                    {'campo_nombre': 'lateralidad', 'campo_label': 'Lateralidad', 'tipo_campo': 'lista', 'obligatorio': True, 'orden': 2, 'opciones': ['Pulmón derecho', 'Pulmón izquierdo']},
                    {'campo_nombre': 'lobulo', 'campo_label': 'Lóbulo', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 3, 'opciones': ['Superior', 'Medio (solo derecho)', 'Inferior', 'Lingular', 'No aplica']},
                    {'campo_nombre': 'dimensiones', 'campo_label': 'Dimensiones del espécimen (cm)', 'tipo_campo': 'texto', 'obligatorio': True, 'orden': 4},
                    {'campo_nombre': 'peso', 'campo_label': 'Peso (g)', 'tipo_campo': 'numero', 'obligatorio': False, 'orden': 5},
                    {'campo_nombre': 'tumor_tamanio', 'campo_label': 'Tamaño del tumor (cm)', 'tipo_campo': 'texto', 'obligatorio': False, 'orden': 6},
                    {'campo_nombre': 'tumor_aspecto', 'campo_label': 'Aspecto macroscópico del tumor', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 7, 'opciones': ['Blanquecino sólido', 'Necrótico', 'Hemorrágico', 'Cavitado', 'Pigmentado']},
                    {'campo_nombre': 'margen_bronquial', 'campo_label': 'Distancia a margen bronquial (cm)', 'tipo_campo': 'texto', 'obligatorio': False, 'orden': 8},
                    {'campo_nombre': 'margen_vascular', 'campo_label': 'Distancia a margen vascular (cm)', 'tipo_campo': 'texto', 'obligatorio': False, 'orden': 9},
                    {'campo_nombre': 'ganglios', 'campo_label': 'Ganglios linfáticos', 'tipo_campo': 'numero', 'obligatorio': False, 'orden': 10},
                    {'campo_nombre': 'pleura', 'campo_label': 'Compromiso pleural', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 11, 'opciones': ['Sin compromiso', 'Retracción pleural', 'Infiltración pleural']},
                    {'campo_nombre': 'observaciones', 'campo_label': 'Observaciones', 'tipo_campo': 'textarea', 'obligatorio': False, 'orden': 12},
                ],
            },
            # ─── 12. RIÑÓN ──────────────────────────────
            {
                'nombre': 'Riñón',
                'descripcion': 'Estudio histopatológico de biopsias renales y nefrectomías.',
                'protocolo_medico': 'En nefrectomías: pesar, medir, seccionar bivalvo. En biopsias: contar glomérulos.',
                'campos': [
                    {'campo_nombre': 'tipo_muestra', 'campo_label': 'Tipo de procedimiento', 'tipo_campo': 'lista', 'obligatorio': True, 'orden': 1, 'opciones': ['Biopsia renal percutánea', 'Nefrectomía radical', 'Nefrectomía parcial', 'Nefroureterectomía']},
                    {'campo_nombre': 'lateralidad', 'campo_label': 'Lateralidad', 'tipo_campo': 'lista', 'obligatorio': True, 'orden': 2, 'opciones': ['Derecho', 'Izquierdo']},
                    {'campo_nombre': 'dimensiones', 'campo_label': 'Dimensiones del riñón (cm)', 'tipo_campo': 'texto', 'obligatorio': True, 'orden': 3},
                    {'campo_nombre': 'peso', 'campo_label': 'Peso (g)', 'tipo_campo': 'numero', 'obligatorio': False, 'orden': 4},
                    {'campo_nombre': 'tumor_presente', 'campo_label': '¿Tumor identificado?', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 5, 'opciones': ['Sí', 'No']},
                    {'campo_nombre': 'tumor_tamanio', 'campo_label': 'Tamaño del tumor (cm)', 'tipo_campo': 'texto', 'obligatorio': False, 'orden': 6},
                    {'campo_nombre': 'tumor_aspecto', 'campo_label': 'Aspecto del tumor', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 7, 'opciones': ['Sólido amarillento', 'Quístico', 'Hemorrágico', 'Necrótico', 'Mixto']},
                    {'campo_nombre': 'capsula_renal', 'campo_label': 'Cápsula renal', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 8, 'opciones': ['Intacta', 'Infiltrada']},
                    {'campo_nombre': 'vena_renal', 'campo_label': 'Vena renal', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 9, 'opciones': ['Libre de tumor', 'Con trombo tumoral', 'No valorable']},
                    {'campo_nombre': 'suprarrenal', 'campo_label': 'Glándula suprarrenal', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 10, 'opciones': ['No incluida', 'Incluida - normal', 'Incluida - con lesión']},
                    {'campo_nombre': 'observaciones', 'campo_label': 'Observaciones', 'tipo_campo': 'textarea', 'obligatorio': False, 'orden': 11},
                ],
            },
            # ─── 13. AMÍGDALAS Y ADENOIDES ───────────────
            {
                'nombre': 'Amígdalas y Adenoides',
                'descripcion': 'Estudio histopatológico de tejido amigdalino y adenoideo.',
                'protocolo_medico': 'Medir cada pieza. Seccionar y describir superficie. Incluir representativos.',
                'campos': [
                    {'campo_nombre': 'tipo_muestra', 'campo_label': 'Tipo de muestra', 'tipo_campo': 'lista', 'obligatorio': True, 'orden': 1, 'opciones': ['Amigdalectomía bilateral', 'Amigdalectomía unilateral', 'Adenoidectomía', 'Amigdalectomía + Adenoidectomía']},
                    {'campo_nombre': 'lateralidad', 'campo_label': 'Lateralidad (amígdalas)', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 2, 'opciones': ['Bilateral', 'Derecha', 'Izquierda', 'No aplica']},
                    {'campo_nombre': 'dimensiones_der', 'campo_label': 'Dimensiones amígdala derecha (cm)', 'tipo_campo': 'texto', 'obligatorio': False, 'orden': 3},
                    {'campo_nombre': 'dimensiones_izq', 'campo_label': 'Dimensiones amígdala izquierda (cm)', 'tipo_campo': 'texto', 'obligatorio': False, 'orden': 4},
                    {'campo_nombre': 'dimensiones_adenoides', 'campo_label': 'Dimensiones adenoides (cm)', 'tipo_campo': 'texto', 'obligatorio': False, 'orden': 5},
                    {'campo_nombre': 'superficie', 'campo_label': 'Superficie', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 6, 'opciones': ['Lisa', 'Criptica', 'Con exudado', 'Hiperplásica']},
                    {'campo_nombre': 'consistencia', 'campo_label': 'Consistencia', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 7, 'opciones': ['Blanda', 'Firme', 'Esponjosa']},
                    {'campo_nombre': 'observaciones', 'campo_label': 'Observaciones', 'tipo_campo': 'textarea', 'obligatorio': False, 'orden': 8},
                ],
            },
            # ─── 14. TEJIDO BLANDO ───────────────────────
            {
                'nombre': 'Tejido Blando',
                'descripcion': 'Estudio de lesiones de tejido blando: lipomas, quistes, tumores de partes blandas.',
                'protocolo_medico': 'Pesar y medir. Seccionar en cortes seriados. Describir consistencia, color y relación con tejidos adyacentes.',
                'campos': [
                    {'campo_nombre': 'tipo_muestra', 'campo_label': 'Tipo de lesión sospechada', 'tipo_campo': 'lista', 'obligatorio': True, 'orden': 1, 'opciones': ['Lipoma', 'Quiste epidérmico', 'Quiste sebáceo', 'Quiste pilonidal', 'Fibroma', 'Neurofibroma', 'Tumor de partes blandas', 'Otro']},
                    {'campo_nombre': 'localizacion', 'campo_label': 'Localización anatómica', 'tipo_campo': 'texto', 'obligatorio': True, 'orden': 2},
                    {'campo_nombre': 'dimensiones', 'campo_label': 'Dimensiones (cm)', 'tipo_campo': 'texto', 'obligatorio': True, 'orden': 3},
                    {'campo_nombre': 'peso', 'campo_label': 'Peso (g)', 'tipo_campo': 'numero', 'obligatorio': False, 'orden': 4},
                    {'campo_nombre': 'capsula', 'campo_label': 'Cápsula', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 5, 'opciones': ['Bien encapsulado', 'Parcialmente encapsulado', 'Sin cápsula definida']},
                    {'campo_nombre': 'color', 'campo_label': 'Color al corte', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 6, 'opciones': ['Amarillento (adiposo)', 'Blanquecino', 'Pardo', 'Grisáceo', 'Hemorrágico']},
                    {'campo_nombre': 'consistencia', 'campo_label': 'Consistencia', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 7, 'opciones': ['Blanda', 'Firme', 'Dura', 'Gelatinosa', 'Mixoide']},
                    {'campo_nombre': 'margenes', 'campo_label': 'Márgenes', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 8, 'opciones': ['Bien definidos', 'Mal definidos', 'Infiltrativos']},
                    {'campo_nombre': 'necrosis', 'campo_label': 'Necrosis', 'tipo_campo': 'lista', 'obligatorio': False, 'orden': 9, 'opciones': ['Presente', 'Ausente']},
                    {'campo_nombre': 'observaciones', 'campo_label': 'Observaciones', 'tipo_campo': 'textarea', 'obligatorio': False, 'orden': 10},
                ],
            },
        ]

        for pdata in patologias_data:
            campos = pdata.pop('campos')
            pat, created = Patologia.objects.get_or_create(
                nombre=pdata['nombre'],
                defaults=pdata,
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'[OK] Patologia "{pat.nombre}" creada'))
                for c in campos:
                    Plantilla.objects.create(patologia=pat, **c)
            else:
                self.stdout.write(f'  Patologia "{pat.nombre}" ya existe, omitida.')

        self.stdout.write(self.style.SUCCESS('\n[DONE] Seed data completo.'))
