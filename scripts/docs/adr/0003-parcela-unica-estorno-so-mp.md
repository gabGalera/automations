# Uma parcela por id e número; estorno é só confirmação MP negativa

O recebível é Id Transação Adquirente + número da parcela. Outra chegada dessa parcela, com valor positivo, substitui as colunas de recebível. Estorno é só `Confirmacao MP` negativa, nasce linha nova sem recebível e não recebe parcela. A parcela desse id entra em outra linha. Fica de fora empilhar a mesma parcela de novo, tratar taxa negativa como estorno e tratar `Status` `Estornado` como linha nova. O financeiro confirmou que estorno é a confirmação negativa do Mercado Pago.
