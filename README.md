<html lang="en">
<body>
    <h1>Проверка сигналов на пробитие уровня сопротивления</h1>
    <p>У нас имеется файл csv с сигналами для сделок в следующем формате:</p>
    <pre>,symbol,emoji,kline,alert_price,Time_(MSK)</pre>
    <p>Необходимо определить был ли пробит уровень сопротивления, его длину (и тем самым его категорию - 1 (0-50 бар), 2 (51-100) или 3 (101-150 )) и максимальный возможный профит с сделки по этому сигналу в %</p>
    <p>Алгоритм нахождения уровня сопротивления следующий:</p>
    <p>Мы получаем историю баров (150 от бара с сигналам, так как 3-я категория включает максимум 150 бар). Затем, сначала проверяем является ли данный бар максимумом (high цена должна быть больше, чем у двух соседних баров по обе стороны).</p>
    <p>В первую очередь мы должны определить конец уровня сопротивления (max_1). Мы передвигаем его в двух случаях:</p>
    <ol>
        <li>Значение для max_1 еще не было установлено</li>
        <li>Если мы уже нашли max_1, то разница в % между high ценой его бара и проверяемого максимума больше 0.1 (данное значение мы регулируем сами и тем самым устанавливаем нужную точность), max_2 (начало уровня сопротивления) еще не устанавливалось ни разу и high цена бара max_1 должна быть меньше цены проверяемого бара (это условие делает возможным передвижение конца уровня сопротивления только вверх, чтобы не было такой ситуации, что не было пробития сразу после окончания уровня сопротивления, но не доходя бара с сигналом. Чтобы пробитием был именно бар с сигналом).</li>
    </ol>
    <p>Если данные условия не выполняются, то мы уже будем устанавливать \ двигать начало уровня сопротивления (max_2). Для этого у нас должны выполняться следующие условия:</p>
    <ol>
        <li>Разница в % между high ценой его бара и проверяемого максимума должная быть меньше или равна 0.06 (данное значение мы регулируем сами и тем самым устанавливаем нужную точность).</li>
        <li>Если разница больше, то мы проверяем будем ли мы проходиться по барам дальше, либо прекратим проверку:
            <ol type="a">
                <li>Мы продолжаем двигаться дальше, если разница high цены проверяемого максимума и max_2 больше 0.06, но меньше 0.1.</li>
                <li>В ином случае, мы прекращаем проверку и заявляем был ли найден уровень.</li>
            </ol>
        </li>
        <li>Помимо этого условия прекращения движения, у нас есть еще одно: если цена проверяемого максимума больше цены, указанной в сигнале.</li>
    </ol>
    <p>В конце мы даем вывод: если max_2 был задан, то уровень был найден и противоположный ответ, если значение так и осталось 0.</p>
    <p>Затем мы формируем отчет в следующем формате:</p>
    <pre>id,is_valid,strength,length,bar_1,bar_2,symbol,profit (%)</pre>
    <p>Для профита мы отправляем еще один запрос к api (но могли сделать все через один. На данный момент посчитал, что так будет оптимально).</p>
    <p>Данные в файл-результат отправляем пачками по 10 записей, дабы меньше нагружать систему.</p>
</body>
</html>
