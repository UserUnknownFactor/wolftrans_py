from wolfrpg import commands, maps, databases, common_events, route
from ruamel.yaml import YAML # NOTE: for debug and string search purposes

yaml_instance = YAML()

yaml_instance.register_class(maps.Map)
yaml_instance.register_class(maps.Map.Event)
yaml_instance.register_class(maps.Map.Event.Page)
yaml_instance.register_class(databases.Database)
yaml_instance.register_class(databases.Database.Type)
yaml_instance.register_class(databases.Database.Field)
yaml_instance.register_class(databases.Database.Data)
yaml_instance.register_class(common_events.CommonEvents)
yaml_instance.register_class(common_events.CommonEvents.Event)
yaml_instance.register_class(commands.Command)
yaml_instance.register_class(commands.Blank)
yaml_instance.register_class(commands.Checkpoint)
yaml_instance.register_class(commands.Message)
yaml_instance.register_class(commands.Choices)
yaml_instance.register_class(commands.Comment)
yaml_instance.register_class(commands.ForceStopMessage)
yaml_instance.register_class(commands.DebugMessage)
yaml_instance.register_class(commands.ClearDebugText)
yaml_instance.register_class(commands.VariableCondition)
yaml_instance.register_class(commands.StringCondition)
yaml_instance.register_class(commands.SetVariable)
yaml_instance.register_class(commands.SetString)
yaml_instance.register_class(commands.InputKey)
yaml_instance.register_class(commands.SetVariableEx)
yaml_instance.register_class(commands.AutoInput)
yaml_instance.register_class(commands.BanInput)
yaml_instance.register_class(commands.Teleport)
yaml_instance.register_class(commands.Sound)
yaml_instance.register_class(commands.Picture)
yaml_instance.register_class(commands.ChangeColor)
yaml_instance.register_class(commands.SetTransition)
yaml_instance.register_class(commands.PrepareTransition)
yaml_instance.register_class(commands.ExecuteTransition)
yaml_instance.register_class(commands.StartLoop)
yaml_instance.register_class(commands.BreakLoop)
yaml_instance.register_class(commands.BreakEvent)
yaml_instance.register_class(commands.EraseEvent)
yaml_instance.register_class(commands.ReturnToTitle)
yaml_instance.register_class(commands.EndGame)
yaml_instance.register_class(commands.StartLoop2)
yaml_instance.register_class(commands.StopNonPic)
yaml_instance.register_class(commands.ResumeNonPic)
yaml_instance.register_class(commands.LoopTimes)
yaml_instance.register_class(commands.Wait)
yaml_instance.register_class(commands.Move) # special case
yaml_instance.register_class(commands.WaitForMove)
yaml_instance.register_class(commands.CommonEvent)
yaml_instance.register_class(commands.CommonEventReserve)
yaml_instance.register_class(commands.SetLabel)
yaml_instance.register_class(commands.JumpLabel)
yaml_instance.register_class(commands.SaveLoad)
yaml_instance.register_class(commands.LoadGame)
yaml_instance.register_class(commands.SaveGame)
yaml_instance.register_class(commands.MoveDuringEventOn)
yaml_instance.register_class(commands.MoveDuringEventOff)
yaml_instance.register_class(commands.Chip)
yaml_instance.register_class(commands.ChipSet)
yaml_instance.register_class(commands.Database)
yaml_instance.register_class(commands.ImportDatabase)
yaml_instance.register_class(commands.Party)
yaml_instance.register_class(commands.MapEffect)
yaml_instance.register_class(commands.ScrollScreen)
yaml_instance.register_class(commands.Effect)
yaml_instance.register_class(commands.CommonEventByName)
yaml_instance.register_class(commands.ChoiceCase)
yaml_instance.register_class(commands.SpecialChoiceCase)
yaml_instance.register_class(commands.ElseCase)
yaml_instance.register_class(commands.CancelCase)
yaml_instance.register_class(commands.LoopEnd)
yaml_instance.register_class(commands.BranchEnd)
yaml_instance.register_class(commands.Default)
yaml_instance.register_class(route.RouteCommand)

def dump(o: object, file_name: str) -> None:
    with open(file_name + ".yaml", mode="w", encoding="utf-8") as f:
        yaml_instance.dump(o, f)

def load(file_name: str) -> object:
    with open(file_name + ".yaml", mode="r", encoding="utf-8") as f:
        return yaml_instance.load(f)
