def get_services_reader(uow: UnitOfWorkDep) -> ServicesReader:
    """Dependência para ler serviços."""
    return ServicesReader(uow=uow)


ServicesReaderDep = Annotated[
    ServicesReader,
    Depends(get_services_reader),
]
