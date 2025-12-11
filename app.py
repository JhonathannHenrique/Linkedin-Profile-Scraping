from flask import Flask, render_template, request, jsonify, send_file
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv
import os, time, random, json, threading
from datetime import datetime
import zipfile
import io

load_dotenv()
EMAIL = os.getenv("LINKEDIN_USER")
SENHA = os.getenv("LINKEDIN_PASS")

app = Flask(__name__)

# Variáveis globais para controlar o status
scraping_status = {
    "running": False,
    "progress": 0,
    "current_profile": "",
    "total_profiles": 0,
    "completed": False,
    "error": None,
    "data": [],
    "pdfs": []
}

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = ""

os.makedirs("screenshots", exist_ok=True)
os.makedirs("linkedin_profiles", exist_ok=True)
os.makedirs("temp_results", exist_ok=True)

def random_delay(min_seconds=1.0, max_seconds=2.5):
    time.sleep(random.uniform(min_seconds, max_seconds))

def human_scroll_search(page):
    try:
        page.wait_for_load_state('networkidle', timeout=5000)
        last_height = page.evaluate("document.body.scrollHeight")
        for _ in range(5):
            page.keyboard.press("End")
            random_delay(2, 3)
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
    except Exception as e:
        print(f"Erro durante a rolagem: {e}")

def human_scroll_profile(page):
    """Rola a página inteira do perfil para carregar todo o conteúdo"""
    try:
        # Rola até o final da página múltiplas vezes para garantir que tudo carregue
        last_height = page.evaluate("document.body.scrollHeight")
        
        for _ in range(8):  # Aumentado para garantir carregamento completo
            page.mouse.wheel(0, random.randint(600, 900))
            random_delay(1.0, 1.5)
            
            # Verifica se chegou ao final
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                # Rola mais um pouco para ter certeza
                page.mouse.wheel(0, 500)
                random_delay(0.5, 1.0)
                break
            last_height = new_height
        
        # Garante que rolou até o final
        page.keyboard.press("End")
        random_delay(1, 2)
        
    except Exception as e:
        print(f"Erro ao rolar perfil: {e}")

def scroll_to_top(page):
    """Rola suavemente até o topo da página"""
    try:
        print("Rolando até o topo da página...")
        # Método 1: JavaScript scroll
        page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        random_delay(1, 1.5)
        
        # Método 2: Tecla Home para garantir
        page.keyboard.press("Home")
        random_delay(1, 1.5)
        
        # Verifica se está no topo
        scroll_position = page.evaluate("window.pageYOffset")
        print(f"Posição de scroll após voltar ao topo: {scroll_position}")
        
    except Exception as e:
        print(f"Erro ao rolar para o topo: {e}")

def extract_full_profile_data(page):
    """Extrai TODAS as informações do perfil do LinkedIn"""
    profile_data = {}
    
    try:
        # ===== INFORMAÇÕES BÁSICAS =====
        try:
            name = page.locator("h1").first.inner_text(timeout=5000)
            profile_data["name"] = name.strip()
        except:
            profile_data["name"] = "N/A"
        
        try:
            headline = page.locator("div.text-body-medium.break-words").first.inner_text(timeout=5000)
            profile_data["headline"] = headline.strip()
        except:
            profile_data["headline"] = "N/A"
        
        # Localização
        try:
            location = page.locator("span.text-body-small.inline.t-black--light.break-words").first.inner_text(timeout=3000)
            profile_data["location"] = location.strip()
        except:
            profile_data["location"] = "N/A"
        
        # ===== SOBRE =====
        try:
            about_section = page.locator('section:has(h2:has-text("Sobre")) div[class*="display-flex"] span[aria-hidden="true"]').first
            about = about_section.inner_text(timeout=5000) if about_section.count() > 0 else "N/A"
            profile_data["about"] = about.strip()
        except:
            profile_data["about"] = "N/A"
        
        # ===== EXPERIÊNCIAS =====
        experiences = []
        try:
            experience_section = page.locator('section:has(h2:has-text("Experiência"))').first
            if experience_section.count() > 0:
                exp_items = experience_section.locator('li.artdeco-list__item').all()
                
                for exp_item in exp_items:
                    try:
                        exp_data = {}
                        
                        # Título do cargo
                        try:
                            title = exp_item.locator('span[aria-hidden="true"]').first.inner_text(timeout=2000)
                            exp_data["title"] = title.strip()
                        except:
                            exp_data["title"] = "N/A"
                        
                        # Empresa
                        try:
                            company = exp_item.locator('span.t-14.t-normal span[aria-hidden="true"]').first.inner_text(timeout=2000)
                            exp_data["company"] = company.strip()
                        except:
                            exp_data["company"] = "N/A"
                        
                        # Período
                        try:
                            date_range = exp_item.locator('span.t-14.t-normal.t-black--light span[aria-hidden="true"]').first.inner_text(timeout=2000)
                            exp_data["date_range"] = date_range.strip()
                        except:
                            exp_data["date_range"] = "N/A"
                        
                        # Localização
                        try:
                            exp_location = exp_item.locator('span.t-14.t-normal.t-black--light span[aria-hidden="true"]').nth(1).inner_text(timeout=2000)
                            exp_data["location"] = exp_location.strip()
                        except:
                            exp_data["location"] = "N/A"
                        
                        # Descrição
                        try:
                            description = exp_item.locator('div[class*="display-flex"] span[aria-hidden="true"]').first.inner_text(timeout=2000)
                            exp_data["description"] = description.strip()
                        except:
                            exp_data["description"] = "N/A"
                        
                        experiences.append(exp_data)
                    except:
                        continue
        except:
            pass
        
        profile_data["experiences"] = experiences
        
        # ===== FORMAÇÃO ACADÊMICA =====
        education = []
        try:
            education_section = page.locator('section:has(h2:has-text("Formação acadêmica"))').first
            if education_section.count() > 0:
                edu_items = education_section.locator('li.artdeco-list__item').all()
                
                for edu_item in edu_items:
                    try:
                        edu_data = {}
                        
                        # Instituição
                        try:
                            school = edu_item.locator('span[aria-hidden="true"]').first.inner_text(timeout=2000)
                            edu_data["school"] = school.strip()
                        except:
                            edu_data["school"] = "N/A"
                        
                        # Grau e curso
                        try:
                            degree = edu_item.locator('span.t-14.t-normal span[aria-hidden="true"]').first.inner_text(timeout=2000)
                            edu_data["degree"] = degree.strip()
                        except:
                            edu_data["degree"] = "N/A"
                        
                        # Período
                        try:
                            date_range = edu_item.locator('span.t-14.t-normal.t-black--light span[aria-hidden="true"]').first.inner_text(timeout=2000)
                            edu_data["date_range"] = date_range.strip()
                        except:
                            edu_data["date_range"] = "N/A"
                        
                        education.append(edu_data)
                    except:
                        continue
        except:
            pass
        
        profile_data["education"] = education
        
        # ===== LICENÇAS E CERTIFICADOS =====
        certifications = []
        try:
            cert_section = page.locator('section:has(h2:has-text("Licenças e certificados"))').first
            if cert_section.count() > 0:
                cert_items = cert_section.locator('li.artdeco-list__item').all()
                
                for cert_item in cert_items:
                    try:
                        cert_data = {}
                        
                        # Nome do certificado
                        try:
                            cert_name = cert_item.locator('span[aria-hidden="true"]').first.inner_text(timeout=2000)
                            cert_data["name"] = cert_name.strip()
                        except:
                            cert_data["name"] = "N/A"
                        
                        # Emissor
                        try:
                            issuer = cert_item.locator('span.t-14.t-normal span[aria-hidden="true"]').first.inner_text(timeout=2000)
                            cert_data["issuer"] = issuer.strip()
                        except:
                            cert_data["issuer"] = "N/A"
                        
                        # Data de emissão
                        try:
                            issue_date = cert_item.locator('span.t-14.t-normal.t-black--light span[aria-hidden="true"]').first.inner_text(timeout=2000)
                            cert_data["issue_date"] = issue_date.strip()
                        except:
                            cert_data["issue_date"] = "N/A"
                        
                        certifications.append(cert_data)
                    except:
                        continue
        except:
            pass
        
        profile_data["certifications"] = certifications
        
        # ===== COMPETÊNCIAS =====
        skills = []
        try:
            skills_section = page.locator('section:has(h2:has-text("Competências"))').first
            if skills_section.count() > 0:
                skill_items = skills_section.locator('div[class*="display-flex"] span[aria-hidden="true"]').all()
                
                for skill_item in skill_items:
                    try:
                        skill_name = skill_item.inner_text(timeout=2000)
                        if skill_name.strip() and len(skill_name.strip()) < 100:  # Filtro básico
                            skills.append(skill_name.strip())
                    except:
                        continue
        except:
            pass
        
        profile_data["skills"] = list(set(skills))[:50]  # Remove duplicatas e limita
        
        # ===== IDIOMAS =====
        languages = []
        try:
            lang_section = page.locator('section:has(h2:has-text("Idiomas"))').first
            if lang_section.count() > 0:
                lang_items = lang_section.locator('li.artdeco-list__item').all()
                
                for lang_item in lang_items:
                    try:
                        lang_data = {}
                        
                        # Nome do idioma
                        try:
                            lang_name = lang_item.locator('span[aria-hidden="true"]').first.inner_text(timeout=2000)
                            lang_data["language"] = lang_name.strip()
                        except:
                            lang_data["language"] = "N/A"
                        
                        # Proficiência
                        try:
                            proficiency = lang_item.locator('span.t-14.t-normal.t-black--light span[aria-hidden="true"]').first.inner_text(timeout=2000)
                            lang_data["proficiency"] = proficiency.strip()
                        except:
                            lang_data["proficiency"] = "N/A"
                        
                        languages.append(lang_data)
                    except:
                        continue
        except:
            pass
        
        profile_data["languages"] = languages
        
        # ===== PROJETOS =====
        projects = []
        try:
            projects_section = page.locator('section:has(h2:has-text("Projetos"))').first
            if projects_section.count() > 0:
                project_items = projects_section.locator('li.artdeco-list__item').all()
                
                for proj_item in project_items:
                    try:
                        proj_data = {}
                        
                        # Nome do projeto
                        try:
                            proj_name = proj_item.locator('span[aria-hidden="true"]').first.inner_text(timeout=2000)
                            proj_data["name"] = proj_name.strip()
                        except:
                            proj_data["name"] = "N/A"
                        
                        # Descrição
                        try:
                            proj_desc = proj_item.locator('div[class*="display-flex"] span[aria-hidden="true"]').first.inner_text(timeout=2000)
                            proj_data["description"] = proj_desc.strip()
                        except:
                            proj_data["description"] = "N/A"
                        
                        projects.append(proj_data)
                    except:
                        continue
        except:
            pass
        
        profile_data["projects"] = projects
        
        # ===== RECOMENDAÇÕES =====
        try:
            recommendations_section = page.locator('section:has(h2:has-text("Recomendações"))').first
            if recommendations_section.count() > 0:
                rec_count = recommendations_section.locator('span.t-bold').first.inner_text(timeout=2000)
                profile_data["recommendations_count"] = rec_count.strip()
        except:
            profile_data["recommendations_count"] = "0"
        
    except Exception as e:
        print(f"Erro ao extrair dados completos: {e}")
    
    return profile_data

def download_profile_as_pdf(page, profile_name, profile_index):
    try:
        print(f"\n=== Procurando botão 'Mais' no perfil {profile_index} ===")
        
        # Lista de seletores baseados na estrutura HTML real fornecida
        more_button_selectors = [
            'button[aria-label="Mais ações"]',  # EXATO do HTML fornecido
            'button:has-text("Mais")',  # Texto do botão
            'button[id*="profile-overflow-action"]',  # ID com parte fixa
            'button.artdeco-dropdown__trigger',  # Classe principal
            '//button[@aria-label="Mais ações"]',  # XPath exato
            '//button[contains(text(), "Mais")]',  # XPath por texto
            '//button[contains(@id, "profile-overflow-action")]'  # XPath por ID
        ]
        
        more_button = None
        found_selector = None
        
        for selector in more_button_selectors:
            try:
                if selector.startswith('//'):
                    more_button = page.locator(f'xpath={selector}')
                else:
                    more_button = page.locator(selector)
                
                if more_button.count() > 0:
                    found_selector = selector
                    print(f"✓ Botão encontrado com seletor: {selector}")
                    print(f"  Quantidade de elementos: {more_button.count()}")
                    
                    # Pega o primeiro elemento visível
                    if more_button.count() > 1:
                        for i in range(more_button.count()):
                            try:
                                if more_button.nth(i).is_visible():
                                    more_button = more_button.nth(i)
                                    print(f"  Usando elemento visível no índice {i}")
                                    break
                            except:
                                continue
                    else:
                        more_button = more_button.first
                    
                    break
            except Exception as e:
                print(f"  ✗ Erro com seletor '{selector}': {str(e)[:80]}")
                continue
        
        if not more_button or not found_selector:
            print("✗ ERRO: Botão 'Mais' não encontrado")
            try:
                page.screenshot(path=f"screenshots/debug_no_more_button_{profile_index}.png")
                print(f"Screenshot salvo: screenshots/debug_no_more_button_{profile_index}.png")
            except:
                pass
            return None
        
        # Garante que o botão está visível
        try:
            more_button.scroll_into_view_if_needed(timeout=5000)
            random_delay(0.5, 1.0)
        except:
            print("Aviso: Não foi possível rolar até o botão")
        
        # Verifica se o botão está realmente visível antes de clicar
        if not more_button.is_visible():
            print("✗ ERRO: Botão 'Mais' não está visível")
            return None
        
        print("Clicando no botão 'Mais'...")
        more_button.click(timeout=5000)
        random_delay(1.5, 2.5)  # Aumentado para garantir que o menu abra
        
        print("Procurando opção 'Salvar como PDF' no menu...")
        
        # Seletores baseados na estrutura HTML real fornecida
        pdf_button_selectors = [
            'div[aria-label="Salvar como PDF"]',  # EXATO do HTML fornecido
            '//div[@aria-label="Salvar como PDF"]',  # XPath exato
            'div.artdeco-dropdown__item:has-text("Salvar como PDF")',
            '//span[text()="Salvar como PDF"]',  # XPath pelo texto do span
            '//div[@role="button" and contains(., "Salvar como PDF")]',
            'span:has-text("Salvar como PDF")',
        ]
        
        pdf_button = None
        found_pdf_selector = None
        
        # Aguarda o menu dropdown aparecer completamente
        try:
            page.wait_for_selector('div.artdeco-dropdown__content', state='visible', timeout=5000)
            print("✓ Menu dropdown está visível")
        except:
            print("⚠ Timeout ao aguardar menu dropdown")
        
        random_delay(1, 1.5)
        
        for selector in pdf_button_selectors:
            try:
                if selector.startswith('//'):
                    pdf_button = page.locator(f'xpath={selector}')
                else:
                    pdf_button = page.locator(selector)
                
                if pdf_button.count() > 0:
                    found_pdf_selector = selector
                    print(f"✓ Opção PDF encontrada com seletor: {selector}")
                    
                    # Pega o primeiro elemento visível
                    if pdf_button.count() > 1:
                        for i in range(pdf_button.count()):
                            try:
                                if pdf_button.nth(i).is_visible():
                                    pdf_button = pdf_button.nth(i)
                                    print(f"  Usando elemento visível no índice {i}")
                                    break
                            except:
                                continue
                    else:
                        pdf_button = pdf_button.first
                    
                    break
            except Exception as e:
                print(f"  ✗ Erro com seletor '{selector}': {str(e)[:80]}")
                continue
        
        if not pdf_button or not found_pdf_selector:
            print("✗ ERRO: Opção 'Salvar como PDF' não encontrada")
            try:
                page.screenshot(path=f"screenshots/debug_no_pdf_option_{profile_index}.png")
                print(f"Screenshot salvo: screenshots/debug_no_pdf_option_{profile_index}.png")
                
                # Tenta listar os itens do menu para debug
                menu_items = page.locator('div.artdeco-dropdown__item').all()
                print(f"Itens encontrados no menu: {len(menu_items)}")
                for i, item in enumerate(menu_items[:10]):
                    try:
                        aria_label = item.get_attribute('aria-label') or 'N/A'
                        print(f"  Item {i}: {aria_label}")
                    except:
                        pass
            except:
                pass
            
            page.keyboard.press("Escape")
            return None
        
        # Verifica se o elemento está visível
        if not pdf_button.is_visible():
            print("✗ ERRO: Opção PDF não está visível")
            page.keyboard.press("Escape")
            return None
        
        print("Clicando em 'Salvar como PDF'...")
        
        # Aguarda o download começar (timeout aumentado)
        try:
            with page.expect_download(timeout=20000) as download_info:
                pdf_button.click(timeout=5000)
                print("✓ Clique executado, aguardando download...")
            
            download = download_info.value
            print(f"✓ Download iniciado: {download.suggested_filename}")
            
            safe_name = "".join(c for c in profile_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name[:50]
            pdf_filename = f"linkedin_profiles/pdf_{profile_index}_{safe_name}.pdf"
            
            download.save_as(pdf_filename)
            print(f"✓ PDF salvo com sucesso: {pdf_filename}")
            random_delay(1, 2)
            return pdf_filename
            
        except PlaywrightTimeoutError:
            print("✗ ERRO: Timeout ao aguardar download do PDF")
            page.keyboard.press("Escape")
            return None
        
    except Exception as e:
        print(f"✗ ERRO ao baixar PDF do perfil {profile_index}: {e}")
        print(f"   Tipo de erro: {type(e).__name__}")
        
        try:
            page.screenshot(path=f"screenshots/error_pdf_download_{profile_index}.png")
            print(f"   Screenshot de erro salvo: screenshots/error_pdf_download_{profile_index}.png")
        except:
            pass
        
        try:
            page.keyboard.press("Escape")
        except:
            pass
        
        return None

def run_scraping(search_term, headless_mode):
    global scraping_status
    
    scraping_status = {
        "running": True,
        "progress": 0,
        "current_profile": "Iniciando...",
        "total_profiles": 0,
        "completed": False,
        "error": None,
        "data": [],
        "pdfs": []
    }
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=headless_mode, 
                executable_path=CHROME_PATH if CHROME_PATH else None,
                args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
                ignore_default_args=["--enable-automation"],
            )
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            scraped_data = []
            pdf_files = []

            # LOGIN
            scraping_status["current_profile"] = "Fazendo login no LinkedIn..."
            page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded", timeout=60000)
            page.locator('input[name="session_key"]').fill(EMAIL)
            random_delay(0.5, 1.0)
            page.locator('input[name="session_password"]').fill(SENHA)
            random_delay(0.5, 1.0)
            page.locator('button[type="submit"]').click()
            page.wait_for_url("**/feed/**", timeout=30000)
            random_delay(2, 3)
            
            # BUSCA
            scraping_status["current_profile"] = f"Buscando por: {search_term}"
            encoded_search_term = search_term.replace(' ', '%20')
            people_search_url = f"https://www.linkedin.com/search/results/people/?keywords={encoded_search_term}&origin=GLOBAL_SEARCH_HEADER"
            page.goto(people_search_url, wait_until="domcontentloaded")
            random_delay(3, 4)
            
            result_selectors = [
                'div[data-view-name="people-search-result"]',
                'ul.reusable-search__entity-result-list',
                'div.search-results__list',
                'li.reusable-search__result-container'
            ]
            
            results_loaded = False
            for selector in result_selectors:
                try:
                    page.wait_for_selector(selector, timeout=10000)
                    results_loaded = True
                    break
                except:
                    continue
            
            if not results_loaded:
                raise Exception("Não foi possível detectar resultados de busca.")
            
            human_scroll_search(page)
            random_delay(2, 3)
            
            # EXTRAÇÃO DE URLs
            scraping_status["current_profile"] = "Coletando URLs dos perfis..."
            profile_urls = page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('a[href*="/in/"]'));
                    const profileLinks = links
                        .map(link => link.href)
                        .filter(href => {
                            const match = href.match(/linkedin\\.com\\/in\\/([^/?]+)/);
                            return match && !href.includes('/company/') && !href.includes('/school/');
                        });
                    return [...new Set(profileLinks)];
                }
            """)
            
            scraping_status["total_profiles"] = len(profile_urls)
            
            # PROCESSAR CADA PERFIL
            for idx, profile_url in enumerate(profile_urls):
                try:
                    clean_url = profile_url.split('?')[0]
                    
                    scraping_status["current_profile"] = f"Processando perfil {idx+1}/{len(profile_urls)}"
                    scraping_status["progress"] = int((idx / len(profile_urls)) * 100)
                    
                    page.goto(clean_url, wait_until="domcontentloaded", timeout=30000)
                    random_delay(2, 3)
                    
                    page.wait_for_selector("h1", timeout=15000)
                    
                    # ROLA A PÁGINA INTEIRA PARA CARREGAR TODO O CONTEÚDO
                    print(f"Rolando perfil {idx+1} para carregar todos os dados...")
                    human_scroll_profile(page)
                    random_delay(2, 3)
                    
                    # EXTRAI TODAS AS INFORMAÇÕES DO PERFIL
                    print(f"Extraindo dados completos do perfil {idx+1}...")
                    person_data = extract_full_profile_data(page)
                    person_data["url"] = clean_url
                    
                    # VOLTA AO TOPO ANTES DE BAIXAR O PDF
                    print(f"Voltando ao topo para baixar PDF do perfil {idx+1}...")
                    scroll_to_top(page)
                    random_delay(2, 3)  # Aumentado o delay para garantir que a página estabilize
                    
                    # AGUARDA O BOTÃO "MAIS" ESTAR DISPONÍVEL
                    try:
                        page.wait_for_selector('button[id*="ember"]', timeout=5000)
                    except:
                        print("Aviso: Timeout ao aguardar botões ember")
                    
                    # DEBUG: Mostra os botões disponíveis (comentar depois se quiser)
                    # debug_page_elements(page, idx+1)
                    
                    # Download PDF
                    print(f"Baixando PDF do perfil {idx+1}...")
                    pdf_path = download_profile_as_pdf(page, person_data.get("name", "unknown"), idx+1)
                    if pdf_path:
                        person_data["pdf_downloaded"] = True
                        pdf_files.append(pdf_path)
                        print(f"PDF baixado com sucesso: {pdf_path}")
                    else:
                        person_data["pdf_downloaded"] = False
                        print(f"Não foi possível baixar o PDF do perfil {idx+1}")
                    
                    scraped_data.append(person_data)
                    random_delay(2, 3)

                except Exception as e:
                    print(f"Erro ao processar perfil {idx+1}: {e}")
            
            scraping_status["data"] = scraped_data
            scraping_status["pdfs"] = pdf_files
            scraping_status["progress"] = 100
            scraping_status["current_profile"] = "Concluído!"
            scraping_status["completed"] = True
            
            # Salva JSON
            timestamp = int(time.time())
            json_filename = f"temp_results/linkedin_profiles_{timestamp}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(scraped_data, f, indent=2, ensure_ascii=False)
            
            scraping_status["json_file"] = json_filename
            
            browser.close()

    except Exception as e:
        scraping_status["error"] = str(e)
        scraping_status["running"] = False
        scraping_status["completed"] = True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    data = request.get_json()
    search_term = data.get('search_term', '')
    show_browser = data.get('show_browser', False) 
    headless_mode = not show_browser 
    
    if not search_term:
        return jsonify({"error": "Campo de busca vazio"}), 400
    
    if scraping_status["running"]:
        return jsonify({"error": "Já existe um scraping em andamento"}), 400
    
    thread = threading.Thread(target=run_scraping, args=(search_term, headless_mode))
    thread.start()
    
    return jsonify({"message": f"Scraping iniciado! (Modo visível: {'Sim' if show_browser else 'Não'})"})

@app.route('/status')
def get_status():
    return jsonify(scraping_status)

@app.route('/download_json')
def download_json():
    if not scraping_status.get("completed"):
        return jsonify({"error": "Scraping ainda não concluído"}), 400
    
    json_data = json.dumps(scraping_status["data"], indent=2, ensure_ascii=False)
    
    buffer = io.BytesIO()
    buffer.write(json_data.encode('utf-8'))
    buffer.seek(0)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'linkedin_profiles_{timestamp}.txt',
        mimetype='text/plain'
    )

@app.route('/download_pdfs')
def download_pdfs():
    if not scraping_status.get("completed"):
        return jsonify({"error": "Scraping ainda não concluído"}), 400
    
    pdf_files = scraping_status.get("pdfs", [])
    
    if not pdf_files:
        return jsonify({"error": "Nenhum PDF foi baixado"}), 404
    
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for pdf_path in pdf_files:
            if os.path.exists(pdf_path):
                zf.write(pdf_path, os.path.basename(pdf_path))
    
    memory_file.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return send_file(
        memory_file,
        as_attachment=True,
        download_name=f'linkedin_pdfs_{timestamp}.zip',
        mimetype='application/zip'
    )

# Status para conexões
connection_status = {
    "running": False,
    "progress": 0,
    "current_profile": "",
    "total_profiles": 0,
    "completed": False,
    "error": None,
    "successful": 0,
    "failed": 0,
    "results": []
}

def send_connection_requests(json_file_path, headless_mode):
    global connection_status
    
    connection_status = {
        "running": True,
        "progress": 0,
        "current_profile": "Iniciando...",
        "total_profiles": 0,
        "completed": False,
        "error": None,
        "successful": 0,
        "failed": 0,
        "results": []
    }
    
    try:
        # Carrega o JSON
        with open(json_file_path, 'r', encoding='utf-8') as f:
            profiles = json.load(f)
        
        connection_status["total_profiles"] = len(profiles)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=headless_mode,
                executable_path=CHROME_PATH if CHROME_PATH else None,
                args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
                ignore_default_args=["--enable-automation"],
            )
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # LOGIN
            connection_status["current_profile"] = "Fazendo login no LinkedIn..."
            page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded", timeout=60000)
            page.locator('input[name="session_key"]').fill(EMAIL)
            random_delay(0.5, 1.0)
            page.locator('input[name="session_password"]').fill(SENHA)
            random_delay(0.5, 1.0)
            page.locator('button[type="submit"]').click()
            page.wait_for_url("**/feed/**", timeout=30000)
            random_delay(2, 3)
            
            # PROCESSAR CADA PERFIL
            for idx, profile in enumerate(profiles):
                profile_url = profile.get("url", "")
                profile_name = profile.get("name", "Unknown")
                
                if not profile_url:
                    connection_status["results"].append({
                        "profile": profile_name,
                        "status": "failed",
                        "reason": "URL não encontrada"
                    })
                    connection_status["failed"] += 1
                    continue
                
                try:
                    connection_status["current_profile"] = f"Conectando com {profile_name} ({idx+1}/{len(profiles)})"
                    connection_status["progress"] = int((idx / len(profiles)) * 100)
                    
                    print(f"\n=== Processando perfil {idx+1}/{len(profiles)}: {profile_name} ===")
                    
                    # Acessa o perfil
                    page.goto(profile_url, wait_until="domcontentloaded", timeout=30000)
                    random_delay(2, 3)
                    
                    # Aguarda a página carregar
                    page.wait_for_selector("h1", timeout=15000)
                    random_delay(1, 2)
                    
                  # Procura o botão "Adicionar" / "Conectar" APENAS na seção principal do perfil
                    # Isso evita pegar os botões da seção "Pessoas que você talvez conheça"
                    connect_button_selectors = [
                        # Seletor mais específico: botão dentro da section principal do perfil
                        'main section.artdeco-card button.artdeco-button--primary:has-text("Adicionar")',
                        'main section button[aria-label*="Convidar"][aria-label*="conectar"].artdeco-button--primary',
                        'main section button:has(svg[data-test-icon="connect-small"])',
                        # XPath específico para a section principal
                        '//main//section[contains(@class, "artdeco-card")]//button[contains(@aria-label, "Convidar") and contains(@aria-label, "conectar")]',
                        '//main//section//button[@class and contains(@class, "artdeco-button--primary") and contains(., "Adicionar")]'
                    ]
                    
                    connect_button = None
                    
                    for selector in connect_button_selectors:
                        try:
                            if selector.startswith('//'):
                                connect_button = page.locator(f'xpath={selector}')
                            else:
                                connect_button = page.locator(selector)
                            
                            if connect_button.count() > 0:
                                # Se houver mais de um, pega o primeiro visível
                                if connect_button.count() > 1:
                                    print(f"⚠ Encontrados {connect_button.count()} botões, pegando o primeiro")
                                    for i in range(min(connect_button.count(), 3)):  # Verifica os 3 primeiros
                                        try:
                                            if connect_button.nth(i).is_visible():
                                                connect_button = connect_button.nth(i)
                                                print(f"✓ Botão 'Adicionar' encontrado (índice {i}) com: {selector}")
                                                break
                                        except:
                                            continue
                                else:
                                    if connect_button.first.is_visible():
                                        print(f"✓ Botão 'Adicionar' encontrado com: {selector}")
                                        connect_button = connect_button.first
                                        break
                        except Exception as e:
                            print(f"  Erro com seletor '{selector}': {str(e)[:80]}")
                            continue
                    
                    if not connect_button:
                        connection_status["results"].append({
                            "profile": profile_name,
                            "status": "skipped",
                            "reason": "Botão 'Adicionar' não encontrado (já conectado ou ação indisponível)"
                        })
                        print(f"⚠ Botão 'Adicionar' não encontrado para {profile_name}")
                        random_delay(1, 2)
                        continue
                    
                    # Clica no botão "Adicionar"
                    print(f"Clicando em 'Adicionar' para {profile_name}...")
                    connect_button.click(timeout=5000)
                    random_delay(2, 3)
                    
                    # Aguarda o modal aparecer
                    try:
                        page.wait_for_selector('div[role="dialog"]', state='visible', timeout=5000)
                        print("✓ Modal de conexão aberto")
                    except:
                        print("⚠ Modal não detectado, mas prosseguindo...")
                    
                    random_delay(1, 2)
                    
                    # Procura o botão "Enviar sem nota"
                    send_button_selectors = [
                        'button[aria-label="Enviar sem nota"]',
                        'button:has-text("Enviar sem nota")',
                        'button.artdeco-button--primary:has-text("Enviar sem nota")',
                        '//button[@aria-label="Enviar sem nota"]',
                        '//button[contains(., "Enviar sem nota")]'
                    ]
                    
                    send_button = None
                    
                    for selector in send_button_selectors:
                        try:
                            if selector.startswith('//'):
                                send_button = page.locator(f'xpath={selector}')
                            else:
                                send_button = page.locator(selector)
                            
                            if send_button.count() > 0 and send_button.first.is_visible():
                                print(f"✓ Botão 'Enviar sem nota' encontrado com: {selector}")
                                send_button = send_button.first
                                break
                        except:
                            continue
                    
                    if not send_button:
                        print(f"✗ Botão 'Enviar sem nota' não encontrado para {profile_name}")
                        # Tenta fechar o modal
                        try:
                            page.keyboard.press("Escape")
                        except:
                            pass
                        
                        connection_status["results"].append({
                            "profile": profile_name,
                            "status": "failed",
                            "reason": "Botão 'Enviar sem nota' não encontrado"
                        })
                        connection_status["failed"] += 1
                        random_delay(1, 2)
                        continue
                    
                    # Clica no botão "Enviar sem nota"
                    print(f"Clicando em 'Enviar sem nota' para {profile_name}...")
                    send_button.click(timeout=5000)
                    random_delay(2, 3)
                    
                    print(f"✓ Convite enviado com sucesso para {profile_name}")
                    
                    connection_status["results"].append({
                        "profile": profile_name,
                        "status": "success",
                        "reason": "Convite enviado com sucesso"
                    })
                    connection_status["successful"] += 1
                    
                    # Delay entre perfis para evitar bloqueio
                    random_delay(3, 5)
                    
                except Exception as e:
                    print(f"✗ Erro ao processar {profile_name}: {e}")
                    connection_status["results"].append({
                        "profile": profile_name,
                        "status": "failed",
                        "reason": str(e)
                    })
                    connection_status["failed"] += 1
                    random_delay(2, 3)
            
            connection_status["progress"] = 100
            connection_status["current_profile"] = "Concluído!"
            connection_status["completed"] = True
            
            browser.close()

    except Exception as e:
        connection_status["error"] = str(e)
        connection_status["running"] = False
        connection_status["completed"] = True

@app.route('/upload_json', methods=['POST'])
def upload_json():
    print("\n=== UPLOAD JSON - INÍCIO ===")
    try:
        print(f"Request files: {request.files}")
        print(f"Request form: {request.form}")
        
        if 'file' not in request.files:
            print("ERRO: 'file' não encontrado em request.files")
            return jsonify({"error": "Nenhum arquivo enviado"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "Nenhum arquivo selecionado"}), 400
        
        if not file.filename.endswith('.json') and not file.filename.endswith('.txt'):
            return jsonify({"error": "Arquivo deve ser JSON ou TXT"}), 400
        
        # Salva o arquivo temporariamente
        timestamp = int(time.time())
        temp_path = f"temp_results/uploaded_{timestamp}.json"
        file.save(temp_path)
        
        # Valida o JSON
        try:
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
                # Tenta carregar como JSON
                profiles = json.loads(content)
            
            if not isinstance(profiles, list):
                os.remove(temp_path)
                return jsonify({"error": "Arquivo deve conter uma lista de perfis (array JSON)"}), 400
            
            if len(profiles) == 0:
                os.remove(temp_path)
                return jsonify({"error": "Arquivo não contém nenhum perfil"}), 400
            
            # Valida se os perfis têm a estrutura básica necessária
            valid_profiles = 0
            for profile in profiles:
                if isinstance(profile, dict) and 'url' in profile:
                    valid_profiles += 1
            
            if valid_profiles == 0:
                os.remove(temp_path)
                return jsonify({"error": "Nenhum perfil válido encontrado (é necessário ter 'url')"}), 400
            
            return jsonify({
                "message": "Arquivo carregado com sucesso",
                "profiles_count": len(profiles),
                "valid_profiles": valid_profiles,
                "file_path": temp_path
            }), 200
        
        except json.JSONDecodeError as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({"error": f"Arquivo JSON inválido: {str(e)}"}), 400
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({"error": f"Erro ao processar arquivo: {str(e)}"}), 400
    
    except Exception as e:
        return jsonify({"error": f"Erro no servidor: {str(e)}"}), 500

@app.route('/start_connections', methods=['POST'])
def start_connections():
    data = request.get_json()
    file_path = data.get('file_path', '')
    show_browser = data.get('show_browser', False)
    headless_mode = not show_browser
    
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "Arquivo não encontrado"}), 400
    
    if connection_status["running"]:
        return jsonify({"error": "Já existe um processo de conexão em andamento"}), 400
    
    thread = threading.Thread(target=send_connection_requests, args=(file_path, headless_mode))
    thread.start()
    
    return jsonify({"message": f"Processo de conexão iniciado! (Modo visível: {'Sim' if show_browser else 'Não'})"})

@app.route('/connection_status')
def get_connection_status():
    return jsonify(connection_status)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
