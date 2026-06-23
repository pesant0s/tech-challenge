CPF_AT_1 = "529.982.247-25"
CPF_AT_2 = "123.456.789-09"
CPF_AT_3 = "000.000.001-91"


def _setup(client, auth_headers, cpf=CPF_AT_1, placa="XYZ-9999"):
    cliente = client.post("/cadastro/clientes", json={
        "nome": "Pedro", "cpf_cnpj": cpf, "telefone": "11999999999"
    }, headers=auth_headers).json()
    veiculo = client.post("/cadastro/veiculos", json={
        "placa": placa, "marca": "Honda", "modelo": "Civic",
        "ano": "2021", "cliente_id": cliente["id"]
    }, headers=auth_headers).json()
    servico = client.post("/catalogo/servicos", json={
        "nome": "Troca de óleo", "preco": 150.00
    }, headers=auth_headers).json()
    return cliente, veiculo, servico


def test_criar_os(client, auth_headers):
    c, v, s = _setup(client, auth_headers)
    r = client.post("/atendimento/os", json={
        "cliente_id": c["id"], "veiculo_id": v["id"],
        "servicos": [{"servico_id": s["id"], "quantidade": 1}]
    }, headers=auth_headers)
    assert r.status_code == 201
    assert r.json()["status"] == "AGUARDANDO_APROVACAO"
    assert float(r.json()["valor_total"]) == 150.0


def test_criar_os_sem_itens(client, auth_headers):
    c, v, _ = _setup(client, auth_headers)
    r = client.post("/atendimento/os", json={
        "cliente_id": c["id"], "veiculo_id": v["id"],
        "servicos": [], "pecas": []
    }, headers=auth_headers)
    assert r.status_code == 422


def test_criar_os_com_peca_apenas(client, auth_headers):
    c, v, _ = _setup(client, auth_headers)
    peca = client.post("/estoque/pecas", json={
        "nome": "Filtro de óleo", "preco": 50.0, "quantidade": 10, "estoque_minimo": 2
    }, headers=auth_headers).json()
    r = client.post("/atendimento/os", json={
        "cliente_id": c["id"], "veiculo_id": v["id"],
        "pecas": [{"peca_id": peca["id"], "quantidade": 1}]
    }, headers=auth_headers)
    assert r.status_code == 201
    assert float(r.json()["valor_total"]) == 50.0


def test_criar_os_servico_e_peca(client, auth_headers):
    c, v, s = _setup(client, auth_headers)
    peca = client.post("/estoque/pecas", json={
        "nome": "Filtro de óleo", "preco": 50.0, "quantidade": 5, "estoque_minimo": 1
    }, headers=auth_headers).json()
    r = client.post("/atendimento/os", json={
        "cliente_id": c["id"], "veiculo_id": v["id"],
        "servicos": [{"servico_id": s["id"], "quantidade": 1}],
        "pecas": [{"peca_id": peca["id"], "quantidade": 2}]
    }, headers=auth_headers)
    assert r.status_code == 201
    assert float(r.json()["valor_total"]) == 150.0 + 50.0 * 2


def test_criar_os_servico_inexistente(client, auth_headers):
    c, v, _ = _setup(client, auth_headers)
    r = client.post("/atendimento/os", json={
        "cliente_id": c["id"], "veiculo_id": v["id"],
        "servicos": [{"servico_id": "00000000-0000-0000-0000-000000000000", "quantidade": 1}]
    }, headers=auth_headers)
    assert r.status_code == 404


def test_consulta_os_por_cpf_publico(client, auth_headers):
    c, v, s = _setup(client, auth_headers)
    client.post("/atendimento/os", json={
        "cliente_id": c["id"], "veiculo_id": v["id"],
        "servicos": [{"servico_id": s["id"], "quantidade": 1}]
    }, headers=auth_headers)
    r = client.get(f"/atendimento/os/consulta?cpf_cnpj={CPF_AT_1}")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_aprovar_os(client, auth_headers):
    c, v, s = _setup(client, auth_headers)
    os = client.post("/atendimento/os", json={
        "cliente_id": c["id"], "veiculo_id": v["id"],
        "servicos": [{"servico_id": s["id"], "quantidade": 1}]
    }, headers=auth_headers).json()
    r = client.post(f"/atendimento/os/{os['id']}/aprovar",
        json={"cpf_cnpj": CPF_AT_1})
    assert r.status_code == 200
    assert r.json()["status"] == "RECEBIDA"


def test_rejeitar_os(client, auth_headers):
    c, v, s = _setup(client, auth_headers)
    os = client.post("/atendimento/os", json={
        "cliente_id": c["id"], "veiculo_id": v["id"],
        "servicos": [{"servico_id": s["id"], "quantidade": 1}]
    }, headers=auth_headers).json()
    r = client.post(f"/atendimento/os/{os['id']}/rejeitar",
        json={"cpf_cnpj": CPF_AT_1})
    assert r.status_code == 200
    assert r.json()["status"] == "NEGADA"


def test_aprovar_os_cpf_errado(client, auth_headers):
    c, v, s = _setup(client, auth_headers)
    os = client.post("/atendimento/os", json={
        "cliente_id": c["id"], "veiculo_id": v["id"],
        "servicos": [{"servico_id": s["id"], "quantidade": 1}]
    }, headers=auth_headers).json()
    r = client.post(f"/atendimento/os/{os['id']}/aprovar",
        json={"cpf_cnpj": CPF_AT_2})
    assert r.status_code == 422


def test_aprovar_os_status_invalido(client, auth_headers):
    c, v, s = _setup(client, auth_headers)
    os = client.post("/atendimento/os", json={
        "cliente_id": c["id"], "veiculo_id": v["id"],
        "servicos": [{"servico_id": s["id"], "quantidade": 1}]
    }, headers=auth_headers).json()
    client.patch(f"/atendimento/os/{os['id']}/status",
        json={"status": "NEGADA"}, headers=auth_headers)
    r = client.post(f"/atendimento/os/{os['id']}/aprovar",
        json={"cpf_cnpj": CPF_AT_1})
    assert r.status_code == 422


def test_listar_os(client, auth_headers):
    c, v, s = _setup(client, auth_headers)
    client.post("/atendimento/os", json={
        "cliente_id": c["id"], "veiculo_id": v["id"],
        "servicos": [{"servico_id": s["id"], "quantidade": 1}]
    }, headers=auth_headers)
    r = client.get("/atendimento/os", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_listar_os_filtro_status(client, auth_headers):
    c, v, s = _setup(client, auth_headers)
    os = client.post("/atendimento/os", json={
        "cliente_id": c["id"], "veiculo_id": v["id"],
        "servicos": [{"servico_id": s["id"], "quantidade": 1}]
    }, headers=auth_headers).json()
    client.patch(f"/atendimento/os/{os['id']}/status",
        json={"status": "RECEBIDA"}, headers=auth_headers)

    r_recebida = client.get("/atendimento/os?status=RECEBIDA", headers=auth_headers)
    assert r_recebida.status_code == 200
    assert len(r_recebida.json()) == 1

    r_diag = client.get("/atendimento/os?status=EM_DIAGNOSTICO", headers=auth_headers)
    assert r_diag.status_code == 200
    assert len(r_diag.json()) == 0


def test_transicao_valida(client, auth_headers):
    c, v, s = _setup(client, auth_headers)
    os = client.post("/atendimento/os", json={
        "cliente_id": c["id"], "veiculo_id": v["id"],
        "servicos": [{"servico_id": s["id"], "quantidade": 1}]
    }, headers=auth_headers).json()
    r = client.patch(f"/atendimento/os/{os['id']}/status",
        json={"status": "RECEBIDA"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "RECEBIDA"


def test_transicao_invalida(client, auth_headers):
    c, v, s = _setup(client, auth_headers)
    os = client.post("/atendimento/os", json={
        "cliente_id": c["id"], "veiculo_id": v["id"],
        "servicos": [{"servico_id": s["id"], "quantidade": 1}]
    }, headers=auth_headers).json()
    r = client.patch(f"/atendimento/os/{os['id']}/status",
        json={"status": "ENTREGUE"}, headers=auth_headers)
    assert r.status_code == 422


def test_fluxo_negacao(client, auth_headers):
    c, v, s = _setup(client, auth_headers)
    os = client.post("/atendimento/os", json={
        "cliente_id": c["id"], "veiculo_id": v["id"],
        "servicos": [{"servico_id": s["id"], "quantidade": 1}]
    }, headers=auth_headers).json()
    r = client.patch(f"/atendimento/os/{os['id']}/status",
        json={"status": "NEGADA"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "NEGADA"
    r2 = client.patch(f"/atendimento/os/{os['id']}/status",
        json={"status": "RECEBIDA"}, headers=auth_headers)
    assert r2.status_code == 422


def test_fluxo_abandono(client, auth_headers):
    c, v, s = _setup(client, auth_headers)
    os = client.post("/atendimento/os", json={
        "cliente_id": c["id"], "veiculo_id": v["id"],
        "servicos": [{"servico_id": s["id"], "quantidade": 1}]
    }, headers=auth_headers).json()
    r = client.patch(f"/atendimento/os/{os['id']}/status",
        json={"status": "ABANDONADA"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "ABANDONADA"


def test_fluxo_completo(client, auth_headers):
    c, v, s = _setup(client, auth_headers)
    os = client.post("/atendimento/os", json={
        "cliente_id": c["id"], "veiculo_id": v["id"],
        "servicos": [{"servico_id": s["id"], "quantidade": 1}]
    }, headers=auth_headers).json()
    os_id = os["id"]
    for status in ["RECEBIDA", "EM_DIAGNOSTICO", "EM_EXECUCAO", "FINALIZADA", "ENTREGUE"]:
        r = client.patch(f"/atendimento/os/{os_id}/status",
            json={"status": status}, headers=auth_headers)
        assert r.status_code == 200
    assert r.json()["status"] == "ENTREGUE"


def test_metricas_sem_os_finalizada(client, auth_headers):
    r = client.get("/atendimento/os/metricas/tempo-medio", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["total_os_finalizadas"] == 0
    assert r.json()["tempo_medio_minutos"] == 0


def test_metricas_tempo_medio(client, auth_headers):
    c, v, s = _setup(client, auth_headers)
    os = client.post("/atendimento/os", json={
        "cliente_id": c["id"], "veiculo_id": v["id"],
        "servicos": [{"servico_id": s["id"], "quantidade": 1}]
    }, headers=auth_headers).json()
    os_id = os["id"]
    for status in ["RECEBIDA", "EM_DIAGNOSTICO", "EM_EXECUCAO", "FINALIZADA"]:
        client.patch(f"/atendimento/os/{os_id}/status",
            json={"status": status}, headers=auth_headers)
    r = client.get("/atendimento/os/metricas/tempo-medio", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["total_os_finalizadas"] == 1
    assert r.json()["tempo_medio_minutos"] >= 0


def test_os_requer_auth(client):
    r = client.post("/atendimento/os", json={
        "cliente_id": "00000000-0000-0000-0000-000000000001",
        "veiculo_id": "00000000-0000-0000-0000-000000000002",
        "servicos": [], "pecas": []
    })
    assert r.status_code == 401


def test_get_os_por_id_publico(client, auth_headers):
    c, v, s = _setup(client, auth_headers)
    os = client.post("/atendimento/os", json={
        "cliente_id": c["id"], "veiculo_id": v["id"],
        "servicos": [{"servico_id": s["id"], "quantidade": 1}]
    }, headers=auth_headers).json()
    r = client.get(f"/atendimento/os/{os['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == os["id"]
    assert r.json()["status"] == "AGUARDANDO_APROVACAO"


def test_get_os_nao_encontrada(client):
    r = client.get("/atendimento/os/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
