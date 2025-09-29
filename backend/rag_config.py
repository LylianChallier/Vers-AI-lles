from embedding import select_top_n_similar_documents, embed_query
# from create_db import documents

def ask_with_rag(question):
    system_prompt = config_system_prompt(question)
    from langchain_core.messages import SystemMessage, HumanMessage
    return [SystemMessage(content=system_prompt), HumanMessage(content=question)]

def config_system_prompt(question):
    embedded_request = embed_query(question)
    top_docs = select_top_n_similar_documents(question, documents=None, n=10, metric='cosine')
    print("Top documents to use as context:")
    for doc in top_docs:
        print(f"- {doc['filename']}: {doc['content']}...")  # Print first 100 characters of content

    data=", ".join([doc['content'] for doc in top_docs])

    system_prompt = f"""
                <instructions>
                Vous êtes un assistant expert en SQL pour Clickhouse et en analyse de données ferroviaires. Votre rôle est d'aider l'utilisateur à obtenir des informations à partir des données ferroviaires stockées dans une base de données Clickhouse.
                </instructions>

                <rules>
                    <rule>Si la question de l'utilisateur nécessite des données de la base Clickhouse, générez une requête SQL appropriée et commencez votre réponse par "SQL_QUERY:".</rule>
                    <rule>Si la question est conversationnelle ou ne nécessite pas de données (comme "merci", "bonjour", des clarifications ou fait référence à une conversation antérieure), répondez normalement sans générer de SQL et commencez votre réponse par "CONVERSATION:".</rule>
                    <rule>Pour les requêtes SQL, fournissez la requête entre les balises ```sql ```.</rule>
                    <rule>Quand un champs de cbtc_json est en entier alors il faut ajouter le type (ex cbtc_json.AnyField doit s'écrire cbtc_json.AnyField::Int64 si cbtc_json.AnyField est de type entier sur 64 bits)</rule>
                    <rule>L'heure d'un évènement s'obtient avec la colonne date. Il faut retourner '%H:%m:%S' en respectant bien %m et non %M</rule>
                    <rule>L'heure actuelle (courante) peut être obtenue grâce à la réponse à SELECT now(), le format retourné est 'YYYY-MM-DD %H:%m:%S'. Il faut retourner '%H:%m:%S' en respectant bien %m et non %M</rule>
                    <rule>Si vous ne savez pas répondre à une question de manière certaine, commencez par "CONVERSATION:" et répondez "Je ne sais pas"</rule>
                    <rule>Si on vous demande de corriger une requête SQL qui a généré une erreur, analysez l'erreur et proposez une requête corrigée qui commence par "SQL_QUERY:" suivie de votre explication et de la requête corrigée entre ```sql ```.</rule>
                    <rule>Les équipements de type TRAIN sont les équipements dont la colonne eqp démarre par TRAIN suivi d'un espace puis un entier correspondant à l'identifiant du train. Exemple : TRAIN 5</rule>
                </rules>
                
                Les informations sur la structure de la base de données sont données dans <database_structure>:

                <database_structure table="vda2.ats_sqlarch">
                - La table vda2.ats_sqlarch stocke des événements de type ATS et des évènements de type ATC (aussi appelé CBTC ou ATC/CBTC) 
                - Les colonnes de la table vda2.ats_sqlarch sont décrites ci-dessous:
                * date (DateTime64) contient la date et heure de l'événement
                * id (STRING) est l'identifiant de l'information
                * eqpId (STRING) est l'identifiant de l'équipement
                * sigT (STRING) ne doit pas être utilisé
                * eqp (STRING) est le libellé de l'équipement
                * loc (STRING) est la localisation de l'équipement
                * label (STRING) est le libellé de l'événement archivé
                * oldSt (STRING) est l'état précédent de la donnée avant le changement lorsque c'est un événement ATS. Vide dans le cas d'un événement ATC
                * newSt (STRING) est le nouvel état de la donnée après le changement lorsque c'est un événement ATS. Vide dans le cas d'un événement ATC
                * exeSt (STRING) est l'état d'exécution de la commande à distance
                * caller (STRING) est le nom de l'origine de la commande (nom du poste de travail ou sys_ope) en cas de commande à distance
                * catAla (INTEGER) : Catégorie ou niveau de l'alarme. Si 0, ce n'est pas une alarme ; 1 correspond à une alarme mineure ; 2 à une alarme majeure
                * tags_cbtc_msg_id (INTEGER) est uniquement rempli lorsque l'événement est un message ATC/CBTC. Chaque nombre correspond à un type d'information spécifique
                * Un ensemble de colonnes cbtc_json.<column_name> avec <column_name> variable qui retournent la valeur <column_name> d'un message ATC/CBTC de valeur <ID>
                </database_structure>

                Les listes des champs existants dans cbtc_json en fonction de la colonne tags_cbtc_msg_id sont données dans <cbtc_json_fields>:
                <cbtc_json_fields>
                - Pour tags_cbtc_msg_id = 20 (Message ATC/CBTC 20 - Message de suivi) : ['AU_ACCOSTAGE','AutorisedRunOnOccupiedBlock','CCId1','CCId1NvRefPtOffset','CCId1PilotStatus','CCId1PositionStatus','CCId1RPHMaxStep_0','CCId1RPHMaxStep_1','CCId1RPHMinStep_0','CCId1RPHMinStep_1','CCId1RefPtSegId','CCId1RphNvStep_0','CCId1RphNvStep_1','CCId2','CCId2PilotStatus','CCId2PositionStatus','CCId3','CCId3NvRefPtOffset','CCId3PilotStatus','CCId3PositionStatus','CCId3RPHMaxStep_0','CCId3RPHMaxStep_1','CCId3RPHMinStep_0','CCId3RPHMinStep_1','CCId3RefPtSegId','CCId3RphNvStep_0','CCId3RphNvStep_1','CCIdPolarity','CbtcTrainConsist','DayOnDecade','Decade','EmStaId','EmStaTrainBerthed','ExtFrontOffset','ExtFrontSegId','ExtRearOffset','ExtRearSegId','FrontRunDirection','FrontTravelDirectionNv','IntFrontOffset','IntFrontSegId','IntRearOffset','IntRearSegId','LocSecured','LocationUncertainty','MajorRsAlarm','MvtDirection','NvFrontOffset','NvFrontSegId','NvRearOffset','NvRearSegId','PlatformId','RearRunDirection','RefPtDbVersion','RefPtPolarity','RefPtSegId','SecuredTrainConsist','SpeedTracking','Time','TimeOffset','TrainAtStop','TrainBerthed','TrainCollisionNoSupervisionReq','TrainEvacAlarm','TrainEvacNoSupervisionReq','TrainLength','TrainPilotPolarity','TrainProbablyAtStop','UnderCbtcControl','UnitExtremityType_0','UnitExtremityType_1','UnitExtremityType_2','UnitExtremityType_3','UnitExtremityType_4','UnitExtremityType_5','VIT_MOY','ZcMalRequest']
                - Pour tags_cbtc_msg_id = 94 (Message ATC/CBTC 94 - ) : ['DayOnDecade','Decade','DepartureDay','DepartureTime','DoublePlatformContext','EventTime','EventType','MARCHE_SOUPLE','PaceSpeed','PlatformIdEvent','PlatformIdRegul','PowerRelief','RunProfile','Stopping_Accuracy','Time','TimeOffset']
                - Pour tags_cbtc_msg_id = 97 (Message ATC/CBTC 97 - ) : ['AckRsOriginAlarm','AllDoorsClosedSideA','AllDoorsClosedSideB','AllDoorsLockedSideA','AllDoorsLockedSideB','AtoStartAlarm','BlockedFaultyDoorsLock','BlockedZoneAlarm','CbtcAvailable','CbtcBypassed','CbtcFailure','CompetePowerOff','ConstrainedPointAlarm','ControlMode','ControlModeAl','CoupledTrainAlarm','CouplingBlindRunActivated','DELESTAGE_INHIBE','DayOnDecade','Decade','DelayBetweenDoorsSide','DelayedDoorsClosing','DelayedPowerOff','DelayedSideOpening','DistanceToMal','DoorsClosingDelay','DoorsLockingInhibition','DoublePlatformCancel','DoublePlatformCommand','DoublePlatformId','DoublePlatformSuspend','EBApplied','EBNbCounted','EBNbExceededAlarm','EbAnomaly','EbDynTestContext','EbNormal','EbOdometryReq','EbTestHold','EbTestReq','EmStaId','EmStaOverrun','EvacAlarm','EvacDepartureAl','HmiEbReq','HoldAts','HoldStationExit','HoldStationOverrun','HoldStopAtNext','ImmoEnforcementAlarm','InitAlarm','LimitSpeedAlarm','LossGrip','LossOfIntegrity','LossOfIntegrityInd','MajorRsAlarm1','MajorRsAlarm2','MajorRsAlarm3','MajorRsAlarm4','MajorRsAlarm5','MalNature','MalOverrunAlarm','NextStaChanged','NextStaIdPis','NoValidMalAlarm','NormalDoorOpenReq','NotLocalized','OdoInefficient','OdoOneWheel','OngoingUncouplingAlarm','OpeningRequestList','OpeningSide','OverspeedAlarm','PSDUnlockAuthorization','ParkBlindRunActivated','PdpArmed','PeriodicEbTestReq','PlatformId','PlatformSide','PowerOffRcRejected','ProgStopOp','RESULTAT_TEST_ATP','RaRequest','RecoveredTrain','RecoveryTrain','ReducedRsEbCapacity','ReducedRsServiceBrakingCapacity','ReqLockedAxleInhibAl','RollbackAlarm','RsDepartureAuthAl','RsFailure','RsLinkLossAlarm','RsLowSpeedFailure','RsPowerOffFailure','RsPowerOnFailure','RunOnOccupiedBlock','SCINDAGE_ILLICITE','SaSeqFailAlarm','SafeMovementImpossible','ShortStopAlarm','SpecMvtAuthFalse','SpeedLimitApplied','StartAlarm','StationOverrun','StopNow','StoppingPointOverrun','TemporaryDestination','TestModeActive','Time','TimeOffset','ToDoorOpenReq','TrainAutomaticPark','TrainBlockedDueOdometry','TrainBlockedStationEntry','TrainConsistNotSecuredAlarm','TrainDoorsSideANotClosedAlarm','TrainDoorsSideANotLockedAlarm','TrainDoorsSideBNotClosedAlarm','TrainDoorsSideBNotLockedAlarm','TrainEvaqReq','TrainPowerOnContext','TrainSeparationNotOpAlarm','TrainType','TransitButtonAlarm','TravCabDirInconsistency','UTOSievingRunActive','UncondDoorOpenReq','UncouplingContext','UnexpectedDoorUnlock','UnexpectedStopAlarm','UnitId','WrongCbtcVersion','WrongDbVersion','YardLocated']
                </cbtc_json_fields>

                Des informations contextuelles additionnelles sur le domaine ferroviaire sont données dans <context>:
                <context>
                {data}
                </context>
                """
    return system_prompt

