def assemble_module(module, html_code, snippets):
    assembled_code = {}
    
    assembled_code["html"] = html_code

    backend_parts = []

    for snippet in snippets:
        backend_parts.append(snippet["code"])

    assembled_code["backend"] = "\n\n".join(backend_parts)

    return assembled_code